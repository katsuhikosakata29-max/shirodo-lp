# -*- coding: utf-8 -*-
"""生成ページ（/100meijo/, /guide/level/）の共通処理。

- 生成物の先頭に「直接編集しない」目印を入れる
- --check でズレを検出する（書き換えずに比較だけ。ズレがあれば終了コード1）
- 更新日を決める（GEN_DATE > --check 時は既存ページの dateModified > 今日）

直接編集したHTMLは次の再生成で消える。--check はそれをコミット前に見つけるためのもの。
"""
import difflib
import os
import re
import sys
from datetime import date

CHECK = "--check" in sys.argv
_DATE_MODIFIED = re.compile(r'"dateModified": "(\d{4}-\d{2}-\d{2})"')


def marker(script_name: str) -> str:
    return (f"<!-- 自動生成ファイル: scripts/{script_name} の出力。直接編集しないこと。"
            f"編集はスクリプト側で行い、再生成する（確認: python3 scripts/{script_name} --check） -->")


def insert_marker(page: str, script_name: str) -> str:
    """<!DOCTYPE html> の直後に目印を入れる（DOCTYPEより前に置くと古いブラウザで互換モードになり得るため）。"""
    head, sep, rest = page.partition("\n")
    assert head.strip().lower() == "<!doctype html>", "生成ページは <!DOCTYPE html> で始まる前提"
    return head + sep + marker(script_name) + "\n" + rest


def date_modified_of(html: str):
    m = _DATE_MODIFIED.search(html)
    return date.fromisoformat(m.group(1)) if m else None


def _read(path: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def resolve_gen_date(out_path: str) -> date:
    if os.environ.get("GEN_DATE"):
        return date.fromisoformat(os.environ["GEN_DATE"])
    if CHECK:
        # 日付だけの違いをズレと誤判定しないよう、公開中ページの更新日で生成して比べる
        existing = date_modified_of(_read(out_path))
        if existing:
            return existing
    return date.today()


def diff_lines(current: str, generated: str, label: str, limit: int = 40) -> list:
    """一致なら空リスト。ズレていれば unified diff の先頭 limit 行。"""
    if current == generated:
        return []
    diff = list(difflib.unified_diff(
        current.splitlines(), generated.splitlines(),
        fromfile=f"{label}（公開中のHTML）", tofile=f"{label}（スクリプトの出力）", lineterm=""))
    return diff[:limit] + ([f"...（残り {len(diff) - limit} 行）"] if len(diff) > limit else [])


def write_or_check(out_path: str, page: str, script_name: str) -> None:
    """通常は書き出す。--check のときは比較だけして終了する（ズレなし=0、ズレあり=1）。"""
    label = os.path.relpath(out_path, os.path.join(os.path.dirname(__file__), ".."))
    if CHECK:
        diff = diff_lines(_read(out_path), page, label)
        if not diff:
            print(f"OK: {label} は {script_name} の出力と一致")
            sys.exit(0)
        print(f"NG: {label} が {script_name} の出力とズレています", file=sys.stderr)
        print("   HTMLが直接編集されたか、生成元データ（アプリの castles.json など）が変わっています。", file=sys.stderr)
        print("   直接編集した内容はスクリプト側に移してから再生成してください。", file=sys.stderr)
        print("\n".join(diff), file=sys.stderr)
        sys.exit(1)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(page)
