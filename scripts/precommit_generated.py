#!/usr/bin/env python3
"""コミット前に、生成ページ（/100meijo/, /guide/level/）の直接編集を止める。

.githooks/pre-commit から呼ばれる。生成ページ・生成スクリプト・生成データが
コミットに含まれるときだけ、各生成スクリプトの --check を実行する。
それ以外のコミット（日次メトリクスの自動コミットなど）は何もせず通す。
"""
import os
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
APP_CASTLES = "/Users/sakatakatsuhiko/Developer/shirodo/native/src/data/castles.json"
GENERATORS = ["scripts/gen_100meijo.py", "scripts/gen_level.py"]
RELEVANT_PREFIXES = ("100meijo/", "guide/level/", "data/")
RELEVANT_FILES = {"scripts/gen_100meijo.py", "scripts/gen_level.py", "scripts/gen_common.py"}


def is_relevant(path: str) -> bool:
    return path in RELEVANT_FILES or path.startswith(RELEVANT_PREFIXES)


def _git_paths(*args: str) -> list:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [p for p in out.splitlines() if p]


def main() -> int:
    staged = [p for p in _git_paths("diff", "--cached", "--name-only") if is_relevant(p)]
    if not staged:
        return 0

    # --check は作業ツリーを見るので、コミットされる中身と作業ツリーが食い違うと正しく判定できない
    unstaged = [p for p in _git_paths("diff", "--name-only") if is_relevant(p)]
    if unstaged:
        print("pre-commit: 生成ページ関連のファイルに、ステージされていない変更があります。", file=sys.stderr)
        print("   正しくズレを判定できないため、git add するか変更を戻してからコミットしてください。", file=sys.stderr)
        for p in unstaged:
            print(f"   - {p}", file=sys.stderr)
        return 1

    if not os.path.exists(APP_CASTLES):
        print(f"pre-commit: 警告 アプリ本体の castles.json が無いため、生成ページのズレ検出をスキップしました（{APP_CASTLES}）",
              file=sys.stderr)
        return 0

    failed = False
    for gen in GENERATORS:
        env = {k: v for k, v in os.environ.items() if k != "GEN_DATE"}
        r = subprocess.run([sys.executable, gen, "--check"], cwd=ROOT, env=env, capture_output=True, text=True)
        if r.returncode != 0:
            failed = True
            sys.stderr.write(r.stdout + r.stderr)
    if failed:
        print("\npre-commit: 生成ページがスクリプトの出力とズレているため、コミットを止めました。", file=sys.stderr)
        print("   直接編集した内容を生成スクリプトに移し、再生成してからコミットしてください（CLAUDE.md 参照）。", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
