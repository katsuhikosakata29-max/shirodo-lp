#!/usr/bin/env python3
"""コミット前に、共通部品（ヘッダー・フッター・head内の共通タグ・共通スクリプト）のズレを止める。

.githooks/pre-commit から呼ばれる。ページのHTMLか共通部品の正本を含むコミットのときだけ
scripts/sync_shared.py --check を実行する。それ以外のコミット（日次メトリクスなど）は素通り。
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SHARED_SOURCES = {"scripts/shared_parts.py", "scripts/sync_shared.py", "assets/site.css"}


def is_relevant(path: str) -> bool:
    return path in SHARED_SOURCES or path.endswith("index.html")


def _git_paths(*args: str) -> list:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p]


def main() -> int:
    if not any(is_relevant(p) for p in _git_paths("diff", "--cached", "--name-only")):
        return 0
    unstaged = [p for p in _git_paths("diff", "--name-only") if is_relevant(p)]
    if unstaged:
        print("pre-commit: ページまたは共通部品に、ステージされていない変更があります。", file=sys.stderr)
        print("   正しく判定できないため、git add するか変更を戻してからコミットしてください。", file=sys.stderr)
        for p in unstaged:
            print(f"   - {p}", file=sys.stderr)
        return 1
    r = subprocess.run([sys.executable, "scripts/sync_shared.py", "--check"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stdout + r.stderr)
        print("\npre-commit: 共通部品がページとズレているため、コミットを止めました。", file=sys.stderr)
        print("   変更は scripts/shared_parts.py に入れ、sync_shared.py の実行と生成ページの再生成をしてからコミットしてください。",
              file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
