"""共通部品（scripts/shared_parts.py）と、各ページへの反映のテスト。"""
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import shared_parts as sp  # noqa: E402
from sync_shared import published_pages  # noqa: E402


class RenderTest(unittest.TestCase):
    def test_page_path(self):
        self.assertEqual(sp.page_path("index.html"), "/")
        self.assertEqual(sp.page_path("guide/level/index.html"), "/guide/level/")

    def test_footer_omits_link_to_current_page(self):
        for href, _ in sp.FOOTER_LINKS:
            with self.subTest(page=href):
                footer = sp.region("footer", href)
                self.assertNotIn(f'href="{href}"', footer)
                self.assertEqual(footer.count("<a href="), len(sp.FOOTER_LINKS) - 1)

    def test_data_note_only_on_top_footer(self):
        self.assertIn("iCloud", sp.region("footer", "/"))
        self.assertNotIn("iCloud", sp.region("footer", "/100meijo/"))

    def test_brand_links_home_except_on_top(self):
        self.assertIn('<div class="nav-brand">', sp.region("nav", "/"))
        self.assertIn('<a class="nav-brand" href="/">', sp.region("nav", "/support/"))

    def test_head_has_smart_app_banner_and_fonts(self):
        head = sp.region("head", "/support/")
        self.assertIn(f'content="app-id={sp.APP_ID}"', head)
        self.assertIn("fonts.googleapis.com/css2", head)

    def test_replace_regions_rejects_missing_marker(self):
        with self.assertRaises(ValueError):
            sp.replace_regions("<html></html>", "/")

    def test_replace_regions_rewrites_stale_content(self):
        stale = "\n".join(f"<!-- shared:{n} -->\n古い中身\n<!-- /shared:{n} -->" for n in sp.REGION_NAMES)
        fresh = sp.replace_regions(stale, "/support/")
        self.assertNotIn("古い中身", fresh)
        self.assertIn("アプリ入手", fresh)


class PublishedPagesTest(unittest.TestCase):
    def test_every_page_has_all_regions_once(self):
        for rel in published_pages():
            html = (ROOT / rel).read_text(encoding="utf-8")
            for name in sp.REGION_NAMES:
                with self.subTest(page=rel, region=name):
                    self.assertEqual(html.count(f"<!-- shared:{name} -->"), 1)

    def test_every_page_is_listed_in_footer(self):
        # 新しいページを作ったら FOOTER_LINKS に足す（足し忘れると他ページから辿れない）
        listed = {href for href, _ in sp.FOOTER_LINKS}
        for rel in published_pages():
            with self.subTest(page=rel):
                self.assertIn(sp.page_path(rel), listed)

    def test_shared_regions_are_up_to_date(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "sync_shared.py"), "--check"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


if __name__ == "__main__":
    unittest.main()
