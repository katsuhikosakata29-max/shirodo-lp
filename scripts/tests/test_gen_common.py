"""gen_common（生成ページの目印・ズレ検出・更新日）のユニットテスト。"""
import os
import subprocess
import sys
import unittest
from datetime import date
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))

import gen_common  # noqa: E402

APP_CASTLES = Path("/Users/sakatakatsuhiko/Developer/shirodo/native/src/data/castles.json")


class MarkerTest(unittest.TestCase):
    def test_marker_goes_right_after_doctype(self):
        page = gen_common.insert_marker("<!DOCTYPE html>\n<html>\n</html>\n", "gen_x.py")
        lines = page.splitlines()
        self.assertEqual(lines[0], "<!DOCTYPE html>")
        self.assertIn("自動生成ファイル: scripts/gen_x.py", lines[1])
        self.assertIn("直接編集しない", lines[1])
        self.assertEqual(lines[2], "<html>")

    def test_rejects_page_without_doctype(self):
        with self.assertRaises(AssertionError):
            gen_common.insert_marker("<html></html>", "gen_x.py")


class DiffTest(unittest.TestCase):
    def test_identical_is_empty(self):
        self.assertEqual(gen_common.diff_lines("a\nb\n", "a\nb\n", "x"), [])

    def test_direct_edit_is_reported(self):
        diff = gen_common.diff_lines("a\n手で追記\nb\n", "a\nb\n", "x")
        self.assertIn("-手で追記", diff)

    def test_long_diff_is_truncated(self):
        cur = "\n".join(str(i) for i in range(200))
        diff = gen_common.diff_lines(cur, "", "x", limit=10)
        self.assertEqual(len(diff), 11)
        self.assertTrue(diff[-1].startswith("...（残り"))


class DateTest(unittest.TestCase):
    def test_reads_date_modified_from_json_ld(self):
        html = '{\n "dateModified": "2026-08-31",\n}'
        self.assertEqual(gen_common.date_modified_of(html), date(2026, 8, 31))

    def test_missing_date_modified(self):
        self.assertIsNone(gen_common.date_modified_of("<html></html>"))


@unittest.skipUnless(APP_CASTLES.exists(), "アプリ本体の castles.json が無い環境では生成できない")
class PublishedPagesMatchGeneratorsTest(unittest.TestCase):
    """公開中の生成ページが、生成スクリプトの出力と一致しているか（直接編集の検出）。"""

    def test_generated_pages_have_no_drift(self):
        for gen in ["gen_100meijo.py", "gen_level.py"]:
            with self.subTest(generator=gen):
                env = {k: v for k, v in os.environ.items() if k != "GEN_DATE"}
                r = subprocess.run([sys.executable, str(SCRIPTS / gen), "--check"],
                                   capture_output=True, text=True, env=env)
                self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
