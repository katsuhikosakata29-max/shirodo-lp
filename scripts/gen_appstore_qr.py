#!/usr/bin/env python3
"""PCで見ている訪問者向けに、App StoreのQRコード（assets/appstore-qr.svg）を生成する。

QRの読み取りはスマホのカメラから直接App Storeへ行くためPostHogには映らない。
効果は App Store Connect の「獲得 > キャンペーン」で LP-QR として確認する。

使い方（qrcode パッケージが必要。サイト本体には含まれない）:
  python3 -m venv /tmp/qrvenv && /tmp/qrvenv/bin/pip install "qrcode==8.0"
  /tmp/qrvenv/bin/python scripts/gen_appstore_qr.py
"""
import os

import qrcode

# App Store Connect で発行したキャンペーンリンク（ct=LP-QR）
URL = "https://apps.apple.com/app/apple-store/id6781983836?pt=129057123&ct=LP-QR&mt=8"
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "appstore-qr.svg")

# 読み取りやすさのため、明るい地に暗いモジュール（サイトの washi / sumi）
BG = "#f2ede2"
FG = "#0a0908"
QUIET = 4  # 規格上の余白（モジュール数）


def build_svg(url: str) -> str:
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=0)
    qr.add_data(url)
    qr.make(fit=True)
    matrix = qr.get_matrix()
    n = len(matrix)
    size = n + QUIET * 2
    path = "".join(
        f"M{c + QUIET} {r + QUIET}h1v1h-1z"
        for r, row in enumerate(matrix)
        for c, dark in enumerate(row)
        if dark
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" '
        f'shape-rendering="crispEdges" role="img" aria-label="城道のApp StoreページのQRコード">'
        f'<rect width="{size}" height="{size}" fill="{BG}"/>'
        f'<path d="{path}" fill="{FG}"/></svg>\n'
    )


if __name__ == "__main__":
    svg = build_svg(URL)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"OK: {os.path.normpath(OUT)} ({len(svg)} bytes)")
