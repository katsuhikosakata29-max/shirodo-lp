"""公開ページの横断チェック。ネットワーク不要。

実行: python3 -m unittest discover scripts/tests
"""
import re
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ANALYTICS_TAG = '<script defer src="/assets/analytics.js"></script>'
QR_TAG = '<script defer src="/assets/appstore-qr.js"></script>'


def published_pages():
    """デプロイ対象の index.html（作業用の .claude 配下などは除く）。"""
    return sorted(
        p for p in ROOT.rglob("index.html")
        if not any(part.startswith(".") for part in p.relative_to(ROOT).parts)
    )


class AppStoreQrTest(unittest.TestCase):
    def test_pages_with_app_store_links_load_qr_script(self):
        pages = [p for p in published_pages() if "apps.apple.com" in p.read_text(encoding="utf-8")]
        self.assertGreater(len(pages), 0)
        for page in pages:
            with self.subTest(page=str(page.relative_to(ROOT))):
                html = page.read_text(encoding="utf-8")
                self.assertIn(QR_TAG, html)
                # PostHogの読み込み後に置く（appstore_qr_open の送信に posthog が要る）
                self.assertLess(html.index(ANALYTICS_TAG), html.index(QR_TAG))

    def test_generators_emit_qr_script(self):
        # 生成ページは再生成で上書きされるので、生成元が共通スクリプト部品を出力している必要がある
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        import shared_parts
        self.assertIn(QR_TAG, shared_parts.region("scripts", "/"))
        for gen in ["gen_100meijo.py", "gen_level.py"]:
            with self.subTest(generator=gen):
                self.assertIn("{SHARED_SCRIPTS}", (ROOT / "scripts" / gen).read_text(encoding="utf-8"))

    def test_qr_svg_is_valid(self):
        svg = ROOT / "assets" / "appstore-qr.svg"
        root = ET.fromstring(svg.read_text(encoding="utf-8"))
        self.assertTrue(root.tag.endswith("svg"))
        self.assertRegex(root.get("viewBox", ""), r"^0 0 \d+ \d+$")

    def test_all_visible_qr_codes_use_campaign_image(self):
        # 計測を揃えるため、ページに置くQRはすべてキャンペーン付きの共通画像にする（素のURLのQRを直書きしない）
        for page in published_pages():
            html = page.read_text(encoding="utf-8")
            with self.subTest(page=str(page.relative_to(ROOT))):
                self.assertNotIn('id="qr-appstore"', html)
                for box in re.findall(r'<div class="qr-box">(.*?)</div>', html, re.S):
                    self.assertIn('src="/assets/appstore-qr.svg"', box)

    def test_qr_generator_uses_campaign_link(self):
        src = (ROOT / "scripts" / "gen_appstore_qr.py").read_text(encoding="utf-8")
        self.assertRegex(src, r"apps\.apple\.com/app/apple-store/id6781983836\?pt=\d+&ct=LP-QR&mt=8")


class HeaderConsistencyTest(unittest.TestCase):
    """ヘッダーは各ページに直書きのため、文言がページごとにずれやすい。"""

    def test_header_cta_text_is_the_same_on_every_page(self):
        texts = {}
        for page in published_pages():
            m = re.search(r'<a class="nav-cta"[^>]*>([^<]*)</a>', page.read_text(encoding="utf-8"))
            if m:
                texts[str(page.relative_to(ROOT))] = m.group(1)
        self.assertGreater(len(texts), 0)
        self.assertEqual(set(texts.values()), {"アプリ入手"}, texts)


class GeneratedMarkerTest(unittest.TestCase):
    def test_generated_pages_carry_do_not_edit_marker(self):
        for page, gen in [("100meijo/index.html", "gen_100meijo.py"), ("guide/level/index.html", "gen_level.py")]:
            with self.subTest(page=page):
                second_line = (ROOT / page).read_text(encoding="utf-8").splitlines()[1]
                self.assertIn(f"自動生成ファイル: scripts/{gen}", second_line)


class HyakumeijoNotationTest(unittest.TestCase):
    """「百名城」表記は主力クエリ対策。生成元から消えると再生成で本番から失われる。"""

    def test_generator_keeps_kanji_notation(self):
        src = (ROOT / "scripts" / "gen_100meijo.py").read_text(encoding="utf-8")
        self.assertRegex(src, r"<title>[^<]*百名城[^<]*</title>")
        self.assertIn("単に<strong>百名城</strong>とも呼ばれます", src)
        self.assertIn("「百名城」と「100名城」は同じですか？", src)

    def test_published_page_keeps_kanji_notation(self):
        html = (ROOT / "100meijo" / "index.html").read_text(encoding="utf-8")
        title = re.search(r"<title>(.*?)</title>", html).group(1)
        self.assertIn("百名城", title)
        self.assertIn("「百名城」と「100名城」は同じですか？", html)


if __name__ == "__main__":
    unittest.main()
