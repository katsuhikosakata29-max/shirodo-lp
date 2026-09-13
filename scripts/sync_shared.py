#!/usr/bin/env python3
"""共通部品（scripts/shared_parts.py）を各ページの目印の間に書き込む。

python3 scripts/sync_shared.py          # 手書きページに反映
python3 scripts/sync_shared.py --check  # 全ページの共通部品が最新かを確認（書き換えない。ズレがあれば終了コード1）

生成ページ（/100meijo/, /guide/level/）は書き換えない。生成スクリプトが同じ部品を読み込むので、
部品を変えたら生成スクリプトを再生成する。--check では生成ページも確認する。
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from gen_common import diff_lines  # noqa: E402
from shared_parts import page_path, replace_regions  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CHECK = "--check" in sys.argv
GENERATED = {"100meijo/index.html": "gen_100meijo.py", "guide/level/index.html": "gen_level.py"}


def published_pages() -> list:
    """デプロイ対象の index.html（ドットで始まるディレクトリは除く）。"""
    pages = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d not in ("node_modules", "scripts")]
        if "index.html" in filenames:
            pages.append(os.path.relpath(os.path.join(dirpath, "index.html"), ROOT))
    return sorted(pages)


def main() -> int:
    drift, pending_regen = [], []
    for rel in published_pages():
        full = os.path.join(ROOT, rel)
        with open(full, encoding="utf-8") as f:
            current = f.read()
        try:
            updated = replace_regions(current, page_path(rel))
        except ValueError as e:
            print(f"NG: {e}", file=sys.stderr)
            drift.append(rel)
            continue
        if updated == current:
            continue
        if CHECK:
            drift.append(rel)
            print("\n".join(diff_lines(current, updated, rel)), file=sys.stderr)
        elif rel in GENERATED:
            pending_regen.append(f"{rel}（python3 scripts/{GENERATED[rel]} で再生成）")
        else:
            with open(full, "w", encoding="utf-8") as f:
                f.write(updated)
            print(f"更新: {rel}")

    if pending_regen:
        print("生成ページは再生成が必要です:\n  " + "\n  ".join(pending_regen))
    if drift:
        print(f"NG: 共通部品が最新でないページ: {', '.join(drift)}", file=sys.stderr)
        print("   目印の間を直接編集した場合は scripts/shared_parts.py に移し、python3 scripts/sync_shared.py を実行してください。",
              file=sys.stderr)
        return 1
    if CHECK:
        print("OK: 全ページの共通部品が最新")
    return 0


if __name__ == "__main__":
    sys.exit(main())
