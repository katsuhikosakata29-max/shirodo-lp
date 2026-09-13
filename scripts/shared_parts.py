# -*- coding: utf-8 -*-
"""全ページ共通のHTML部品の正本（head内の共通タグ・ヘッダー・フッター・共通スクリプト）。

各ページには次の目印があり、目印の間はここから書き込まれる。目印の間を直接編集しないこと。
  <!-- shared:head --> ... <!-- /shared:head -->
  <!-- shared:nav --> ... <!-- /shared:nav -->
  <!-- shared:footer --> ... <!-- /shared:footer -->
  <!-- shared:scripts --> ... <!-- /shared:scripts -->

手書きページへの反映は scripts/sync_shared.py、生成ページは各生成スクリプトが読み込む。
新しいページを作ったら FOOTER_LINKS に追加し、4つの目印を置いて sync_shared.py を実行する。
"""
import hashlib
import os
import re

APP_ID = "6781983836"
APP_STORE_URL = f"https://apps.apple.com/app/id{APP_ID}"

FAVICON = ('<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 '
           'viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>🏯</text></svg>">')
# 全ページで使う書体・太さの和集合（CSSの --f-serif / --f-sans が参照する3書体）
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@400;500;600;700"
             "&family=Noto+Sans+JP:wght@400;500;700&family=Shippori+Mincho:wght@500;600;700&display=swap")

# フッターのリンク（表示順）。各ページでは自分自身へのリンクを外す
FOOTER_LINKS = [
    ("/", "トップページ"),
    ("/shindan/", "城めぐりタイプ診断"),
    ("/100meijo/", "日本100名城 一覧"),
    ("/guide/mochimono/", "城巡りの持ち物ガイド"),
    ("/guide/level/", "登城難易度一覧"),
    ("/guide/kiroku/", "登城記録のつけ方"),
    ("/support/", "サポート"),
    ("/privacy/", "プライバシーポリシー"),
]
# トップのフッターだけに出す一文（アプリのデータの扱い。LP自体は計測しているので読み物ページには出さない）
TOP_FOOTER_NOTE = "すべての記録は、あなたの端末とあなたのiCloudにのみ保存されます。<br>アカウント登録・広告・トラッキングはありません。"

REGION_NAMES = ("head", "nav", "footer", "scripts")
SITE_CSS = os.path.join(os.path.dirname(__file__), "..", "assets", "site.css")


def site_css_version() -> str:
    """共通CSSの中身から作る版番号。CSSを変えると全ページの読み込みURLが変わり、ブラウザやCDNの古いキャッシュを避けられる。"""
    with open(SITE_CSS, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()[:8]


def page_path(rel_file: str) -> str:
    """'index.html' → '/'、'guide/level/index.html' → '/guide/level/'"""
    d = rel_file[: -len("index.html")]
    return "/" + d


def _head(path: str) -> str:
    return "\n".join([
        f'<meta name="apple-itunes-app" content="app-id={APP_ID}">',
        FAVICON,
        '<link rel="preconnect" href="https://fonts.googleapis.com">',
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>',
        f'<link rel="stylesheet" href="{FONTS_URL}">',
        # ページ固有の <style> より前に読み込み、同じセレクタはページ側が上書きできるようにする
        f'<link rel="stylesheet" href="/assets/site.css?v={site_css_version()}">',
    ])


def _nav(path: str) -> str:
    # トップでは自分自身へのリンクにしない
    brand = ('<div class="nav-brand">城道<small>SHIRODO</small></div>' if path == "/"
             else '<a class="nav-brand" href="/">城道<small>SHIRODO</small></a>')
    return "\n".join([
        '<nav class="nav">',
        f"  {brand}",
        f'  <a class="nav-cta" href="{APP_STORE_URL}">アプリ入手</a>',
        "</nav>",
    ])


def _footer(path: str) -> str:
    links = [f'<a href="{href}">{label}</a>' for href, label in FOOTER_LINKS if href != path]
    lines = ["<footer>", '  <span class="footer-brand">城道 SHIRODO</span>']
    if path == "/":
        lines.append(f"  <p>{TOP_FOOTER_NOTE}</p>")
    lines.append("  <p>")
    lines.append(f"    {links[0]}")
    lines += [f"    &nbsp;·&nbsp; {a}" for a in links[1:]]
    lines += ["    &nbsp;·&nbsp; © 2026 城道（SHIRODO）", "  </p>", "</footer>"]
    return "\n".join(lines)


def _scripts(path: str) -> str:
    return "\n".join([
        '<script defer src="/assets/analytics.js"></script>',
        '<script defer src="/assets/appstore-qr.js"></script>',
    ])


_RENDERERS = {"head": _head, "nav": _nav, "footer": _footer, "scripts": _scripts}


def region(name: str, path: str) -> str:
    """目印込みの共通部品。"""
    return f"<!-- shared:{name} -->\n{_RENDERERS[name](path)}\n<!-- /shared:{name} -->"


def _region_pattern(name: str):
    return re.compile(rf"<!-- shared:{name} -->\n.*?\n<!-- /shared:{name} -->", re.S)


def replace_regions(html: str, path: str) -> str:
    """ページ内の目印の間を、最新の共通部品で置き換える。目印が無い・重複している場合は例外。"""
    for name in REGION_NAMES:
        pattern = _region_pattern(name)
        count = len(pattern.findall(html))
        if count != 1:
            raise ValueError(f"{path}: 目印 shared:{name} が {count} 個あります（1個必要）")
        html = pattern.sub(lambda _m, n=name: region(n, path), html)
    return html
