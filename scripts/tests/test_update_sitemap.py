# -*- coding: utf-8 -*-
"""update_sitemap.py の純粋関数のテスト。

    python3 -m unittest discover scripts/tests
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import update_sitemap as us  # noqa: E402


SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"
        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">
  <url>
    <loc>https://shirodo.com/</loc>
    <lastmod>2026-07-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>1.0</priority>
    <image:image>
      <image:loc>https://shirodo.com/assets/a.jpg</image:loc>
      <image:title>写真</image:title>
    </image:image>
  </url>
  <url>
    <loc>https://shirodo.com/guide/kiroku/</loc>
    <lastmod>2026-07-01</lastmod>
    <changefreq>monthly</changefreq>
    <priority>0.7</priority>
  </url>
</urlset>
"""


class TestUrlToPath(unittest.TestCase):
    def test_root(self):
        self.assertEqual(us.url_to_path("https://shirodo.com/"), "index.html")

    def test_nested_dir(self):
        self.assertEqual(
            us.url_to_path("https://shirodo.com/guide/kiroku/"), "guide/kiroku/index.html"
        )

    def test_file_url_kept_as_is(self):
        self.assertEqual(us.url_to_path("https://shirodo.com/robots.txt"), "robots.txt")

    def test_external_url_rejected(self):
        with self.assertRaises(ValueError):
            us.url_to_path("https://example.com/")


class TestSync(unittest.TestCase):
    def setUp(self):
        # 実ファイルの存在チェックを迂回するため、リポジトリ直下を一時的に差し替える
        self._orig_repo = us.REPO
        us.REPO = Path(__file__).resolve().parent / "_fixture"
        (us.REPO / "guide" / "kiroku").mkdir(parents=True, exist_ok=True)
        (us.REPO / "index.html").write_text("", encoding="utf-8")
        (us.REPO / "guide" / "kiroku" / "index.html").write_text("", encoding="utf-8")

    def tearDown(self):
        import shutil
        shutil.rmtree(us.REPO, ignore_errors=True)
        us.REPO = self._orig_repo

    def test_updates_only_stale_lastmod(self):
        dates = {"index.html": "2026-07-21", "guide/kiroku/index.html": "2026-07-01"}
        new_text, changes, warnings = us.sync(SAMPLE, lambda p: dates[p])
        self.assertEqual(warnings, [])
        self.assertEqual(changes, [("https://shirodo.com/", "2026-07-01", "2026-07-21")])
        self.assertIn("<lastmod>2026-07-21</lastmod>", new_text)
        # 変更のない方は据え置き
        self.assertEqual(new_text.count("<lastmod>2026-07-01</lastmod>"), 1)

    def test_preserves_image_block_and_layout(self):
        new_text, _, _ = us.sync(SAMPLE, lambda p: "2026-07-21")
        self.assertIn("<image:title>写真</image:title>", new_text)
        self.assertIn('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"', new_text)
        # lastmod 以外の行数が変わっていないこと
        self.assertEqual(len(SAMPLE.splitlines()), len(new_text.splitlines()))

    def test_warns_when_file_missing(self):
        (us.REPO / "guide" / "kiroku" / "index.html").unlink()
        _, changes, warnings = us.sync(SAMPLE, lambda p: "2026-07-21")
        self.assertEqual(len(warnings), 1)
        self.assertIn("guide/kiroku/index.html", warnings[0])
        # 欠損ページは変更対象から外れる
        self.assertEqual([c[0] for c in changes], ["https://shirodo.com/"])


if __name__ == "__main__":
    unittest.main()
