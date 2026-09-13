"""共通CSS（assets/site.css）のテスト。"""
import re
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1]
ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

import shared_parts as sp  # noqa: E402
from sync_shared import published_pages  # noqa: E402

SITE_CSS = ROOT / "assets" / "site.css"


def top_level_rules(css: str):
    """@media の外にある規則を (セレクタ, 正規化した規則全体) で返す。"""
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    rules, depth, start = [], 0, 0
    for i, ch in enumerate(css):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                text = css[start:i + 1].strip()
                if text and not text.startswith("@"):
                    sel = re.sub(r"\s+", " ", text[:text.index("{")]).strip()
                    rules.append((sel, re.sub(r"\s+", " ", text)))
                start = i + 1
    return rules


class SiteCssTest(unittest.TestCase):
    def test_every_page_loads_current_version(self):
        link = f'<link rel="stylesheet" href="/assets/site.css?v={sp.site_css_version()}">'
        for rel in published_pages():
            with self.subTest(page=rel):
                self.assertIn(link, (ROOT / rel).read_text(encoding="utf-8"))

    def test_site_css_loads_before_page_styles(self):
        # ページ固有の <style> が同じセレクタを上書きできる順序になっていること
        for rel in published_pages():
            html = (ROOT / rel).read_text(encoding="utf-8")
            with self.subTest(page=rel):
                self.assertLess(html.index("/assets/site.css"), html.index("<style"))

    def test_core_tokens_defined(self):
        css = SITE_CSS.read_text(encoding="utf-8")
        for token in ["--gold", "--sumi", "--washi", "--washi-dim", "--line", "--f-serif", "--f-sans"]:
            with self.subTest(token=token):
                self.assertRegex(css, rf"{re.escape(token)}\s*:")

    def test_pages_do_not_repeat_shared_rules(self):
        # 共通CSSと同じ規則をページにも書くと、また二重管理になる
        shared = {full for _, full in top_level_rules(SITE_CSS.read_text(encoding="utf-8"))}
        for rel in published_pages():
            html = (ROOT / rel).read_text(encoding="utf-8")
            inline = "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))
            with self.subTest(page=rel):
                dup = [sel for sel, full in top_level_rules(inline) if full in shared]
                self.assertEqual(dup, [])


if __name__ == "__main__":
    unittest.main()
