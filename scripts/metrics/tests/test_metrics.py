"""report / fetch_asc(パース) / common(upsert) / run_daily(git) のユニットテスト。ネットワーク不要。"""
import datetime
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import common
import report
from fetch_asc import parse_sales_tsv
from run_daily import commit_and_push

TODAY = datetime.date(2026, 7, 8)


def daily(date, clicks, impressions):
    return {"date": date, "clicks": str(clicks), "impressions": str(impressions)}


class TestReport(unittest.TestCase):
    def test_week_over_week(self):
        rows = [
            daily("2026-07-07", 3, 10),   # 直近7日
            daily("2026-07-01", 1, 5),    # 直近7日 (境界内)
            daily("2026-06-30", 2, 8),    # 前週
            daily("2026-06-24", 1, 2),    # 前週 (境界内)
            daily("2026-06-23", 9, 99),   # 範囲外
        ]
        cur, prev = report.week_over_week(rows, "clicks", TODAY)
        self.assertEqual((cur, prev), (4, 3))
        cur, prev = report.week_over_week(rows, "impressions", TODAY)
        self.assertEqual((cur, prev), (15, 10))

    def test_build_digest_full(self):
        gsc = [daily("2026-07-05", 1, 8), daily("2026-07-04", 1, 5)]
        asc = [{"date": "2026-07-06", "first_downloads": "6",
                "redownloads": "2", "updates": "3"}]
        queries = [{"query": "城道", "clicks": 1, "impressions": 4}]
        pages = [{"page": "https://shirodo.com/", "clicks": 2, "impressions": 9}]
        md = report.build_digest(gsc, queries, pages, asc, TODAY)
        self.assertIn("直近7日クリック数: **2**", md)
        self.assertIn("直近7日初回DL: **6**", md)
        self.assertIn("| 城道 | 1 | 4 |", md)
        self.assertIn("最新日 2026-07-05", md)

    def test_build_digest_empty_sources(self):
        md = report.build_digest([], [], [], [], TODAY, errors=["GSC: boom"])
        self.assertIn("データ未取得", md)
        self.assertIn("GSC: boom", md)

    def test_notification_summary(self):
        gsc = [daily("2026-07-05", 2, 14)]
        asc = [{"date": "2026-07-06", "first_downloads": "6",
                "redownloads": "2", "updates": "3"}]
        s = report.notification_summary(gsc, asc, TODAY)
        self.assertEqual(s, "GSC 7日: クリック2/表示14 | App 7日: DL6")


class TestAscParse(unittest.TestCase):
    def test_parse_sales_tsv(self):
        tsv = (
            "Provider\tProduct Type Identifier\tUnits\n"
            "APPLE\t1F\t5\n"      # 初回DL
            "APPLE\t1\t1\n"       # 初回DL
            "APPLE\t3F\t2\n"      # 再DL
            "APPLE\t7F\t3\n"      # アップデート
        )
        totals = parse_sales_tsv(tsv)
        self.assertEqual(totals, {"first_downloads": 6,
                                  "redownloads": 2, "updates": 3})

    def test_parse_ignores_bad_units(self):
        tsv = ("Provider\tProduct Type Identifier\tUnits\n"
               "APPLE\t1F\tabc\n")
        totals = parse_sales_tsv(tsv)
        self.assertEqual(totals["first_downloads"], 0)


class TestUpsertCsv(unittest.TestCase):
    def test_upsert_overwrites_same_date(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "x.csv"
            fields = ["date", "clicks", "impressions"]
            common.upsert_csv(path, fields, [daily("2026-07-04", 1, 5)])
            common.upsert_csv(path, fields, [daily("2026-07-04", 2, 6),
                                             daily("2026-07-05", 1, 8)])
            rows = common.read_csv(path)
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["clicks"], "2")  # 上書きされている
            self.assertEqual(rows[1]["date"], "2026-07-05")


class TestCommitAndPush(unittest.TestCase):
    def _init_repo(self, d):
        root = Path(d)
        for cmd in (["git", "init", "-q", "-b", "main"],
                    ["git", "config", "user.email", "test@example.com"],
                    ["git", "config", "user.name", "test"]):
            subprocess.run(cmd, cwd=root, check=True, capture_output=True)
        (root / "metrics").mkdir()
        return root

    def _git(self, root, *args):
        return subprocess.run(["git", "-C", str(root), *args],
                              capture_output=True, text=True)

    def test_commits_metrics_and_reports_push_failure(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._init_repo(d)
            (root / "metrics" / "gsc_daily.csv").write_text("date,clicks\n")
            (root / "other.txt").write_text("触らない")  # metrics外は対象外
            errors = commit_and_push(TODAY, repo_root=root)
            # リモートがないのでpushだけ失敗し、コミットは残る
            self.assertEqual(len(errors), 1)
            self.assertIn("git push", errors[0])
            log = self._git(root, "log", "--oneline").stdout
            self.assertIn("chore(metrics): 2026-07-08 の日次データ", log)
            status = self._git(root, "status", "--porcelain").stdout
            self.assertIn("?? other.txt", status)  # metrics外は未コミットのまま

    def test_no_changes_is_noop(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._init_repo(d)
            (root / "metrics" / "gsc_daily.csv").write_text("date,clicks\n")
            commit_and_push(TODAY, repo_root=root)
            self.assertEqual(commit_and_push(TODAY, repo_root=root), [])

    def test_skips_on_non_main_branch(self):
        with tempfile.TemporaryDirectory() as d:
            root = self._init_repo(d)
            (root / "metrics" / "gsc_daily.csv").write_text("date,clicks\n")
            self._git(root, "add", "-A")
            self._git(root, "commit", "-m", "init")
            self._git(root, "checkout", "-q", "-b", "feature")
            (root / "metrics" / "gsc_daily.csv").write_text("date,clicks\n2026-07-08,1\n")
            self.assertEqual(commit_and_push(TODAY, repo_root=root), [])
            log = self._git(root, "log", "--oneline").stdout
            self.assertNotIn("chore(metrics)", log)


if __name__ == "__main__":
    unittest.main()
