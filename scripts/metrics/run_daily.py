"""日次メトリクス収集のエントリポイント。

毎朝launchdから実行される想定。手動実行も可:
  .venv/bin/python run_daily.py [--notify]

GSC/ASCそれぞれ独立して取得し、片方が失敗してももう片方は反映する。
結果は metrics/*.csv に蓄積し、metrics/DAILY.md にダイジェストを書く。
取得後、metrics/ の変更を自動で main にコミットしてプッシュする
(リモート＝SEO_LOGの週次判定の材料をこのMacの外からも見られるようにするため)。
"""
import argparse
import datetime
import subprocess
import sys

from common import load_config, upsert_csv, read_csv, METRICS_DIR, REPO_ROOT
import report

GSC_DAILY_CSV = METRICS_DIR / "gsc_daily.csv"
GSC_QUERIES_CSV = METRICS_DIR / "gsc_queries.csv"
GSC_PAGES_CSV = METRICS_DIR / "gsc_pages.csv"
ASC_DAILY_CSV = METRICS_DIR / "asc_daily.csv"
DIGEST_MD = METRICS_DIR / "DAILY.md"


def collect(today):
    config = load_config()
    errors = []
    gsc_queries, gsc_pages = [], []

    if "gsc" in config:
        try:
            import fetch_gsc
            data = fetch_gsc.fetch(config["gsc"], today)
            upsert_csv(GSC_DAILY_CSV,
                       ["date", "clicks", "impressions", "position"],
                       data["daily"])
            gsc_queries = sorted(data["queries"],
                                 key=lambda r: (-r["clicks"], -r["impressions"]))
            gsc_pages = sorted(data["pages"],
                               key=lambda r: (-r["clicks"], -r["impressions"]))
            # クエリ/ページはスナップショットとして取得日付きで履歴も残す
            upsert_csv(GSC_QUERIES_CSV,
                       ["date", "query", "clicks", "impressions", "position"],
                       [{"date": f"{today.isoformat()}|{q['query']}", **q}
                        for q in gsc_queries])
            upsert_csv(GSC_PAGES_CSV,
                       ["date", "page", "clicks", "impressions", "position"],
                       [{"date": f"{today.isoformat()}|{p['page']}", **p}
                        for p in gsc_pages])
        except Exception as e:  # noqa: BLE001 - 片系failでも他系は続行
            errors.append(f"GSC: {e}")
    else:
        errors.append("GSC: 未設定 (config.jsonにgscセクションがない)")

    if "asc" in config:
        try:
            import fetch_asc
            rows = fetch_asc.fetch(config["asc"], today)
            if rows:
                upsert_csv(ASC_DAILY_CSV,
                           ["date", "first_downloads", "redownloads", "updates"],
                           rows)
        except Exception as e:  # noqa: BLE001
            errors.append(f"ASC: {e}")
    else:
        errors.append("ASC: 未設定 (config.jsonにascセクションがない)")

    return gsc_queries, gsc_pages, errors


def commit_and_push(today, repo_root=REPO_ROOT):
    """metrics/ の変更だけを main 上でコミットしてプッシュする。

    - 作業コピーが main 以外のブランチなら何もしない(作業中ブランチを汚さない。
      変更は作業ツリーに残り、次に main で実行されたときにまとめてコミットされる)
    - metrics/ 以外の未コミット変更・ステージ内容には触れない(pathspec付きcommit)
    - push失敗はエラー文字列として返すだけ(コミットは残るので翌日のpushで回収される)

    戻り値: エラーメッセージのリスト(空なら成功またはスキップ/変更なし)
    """
    def git(*cmd_args, check=True):
        return subprocess.run(["git", "-C", str(repo_root), *cmd_args],
                              capture_output=True, text=True, check=check)

    # --show-current は初回コミット前でも動く。detached HEADでは空文字→スキップ
    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        print(f"git: ブランチが {branch} のためコミットをスキップ"
              "(mainに戻った後の実行で反映される)", file=sys.stderr)
        return []

    git("add", "-A", "--", "metrics")
    if git("diff", "--cached", "--quiet", "--", "metrics",
           check=False).returncode == 0:
        return []

    commit = git("commit",
                 "-m", f"chore(metrics): {today.isoformat()} の日次データ",
                 "--", "metrics", check=False)
    if commit.returncode != 0:
        return [f"git commit: {commit.stderr.strip()}"]

    push = git("push", "origin", "main", check=False)
    if push.returncode != 0:
        return [f"git push: {push.stderr.strip()} (コミット済み。翌日以降のpushで回収される)"]
    return []


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--notify", action="store_true",
                        help="macOS通知を出す(launchd実行用)")
    parser.add_argument("--no-git", action="store_true",
                        help="metrics/ の自動コミット&プッシュをしない")
    args = parser.parse_args()

    today = datetime.date.today()
    gsc_queries, gsc_pages, errors = collect(today)

    gsc_daily = read_csv(GSC_DAILY_CSV)
    asc_daily = read_csv(ASC_DAILY_CSV)

    digest = report.build_digest(gsc_daily, gsc_queries, gsc_pages,
                                 asc_daily, today, errors=errors)
    METRICS_DIR.mkdir(parents=True, exist_ok=True)
    DIGEST_MD.write_text(digest)
    print(digest)

    if not args.no_git:
        errors.extend(commit_and_push(today))

    if errors:
        print("errors:", errors, file=sys.stderr)

    if args.notify:
        summary = report.notification_summary(gsc_daily, asc_daily, today)
        if errors:
            summary += " ⚠️一部エラー"
        subprocess.run([
            "osascript", "-e",
            f'display notification "{summary}" with title "SHIRODO メトリクス"',
        ], check=False)

    return 1 if errors and not (gsc_daily or asc_daily) else 0


if __name__ == "__main__":
    sys.exit(main())
