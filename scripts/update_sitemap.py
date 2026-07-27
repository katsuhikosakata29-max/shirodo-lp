# -*- coding: utf-8 -*-
"""sitemap.xml の <lastmod> を各ページの実際の更新日に同期する。

    python3 scripts/update_sitemap.py          # 同期して書き換える
    python3 scripts/update_sitemap.py --check  # ズレていたら終了コード1（書き換えない）

lastmod の決め方:
  - 未コミットの変更があるファイル → 今日（これから同じ内容をコミットする前提）
  - それ以外                       → そのファイルの最終コミット日

ページ本体は書き換えない。sitemap.xml の lastmod の値だけを差し替えるため、
image:image ブロックやインデントはそのまま残る。
"""
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SITEMAP = REPO / "sitemap.xml"
SITE_ROOT = "https://shirodo.com/"

# sitemap に載せない index.html（掲載漏れ検出の対象外）。
# これに加えてドット始まりのディレクトリ（.git / .claude/worktrees など）も一律で除外する。
IGNORED_DIRS = {"node_modules", "scripts", "assets", "docs", "metrics"}


def url_to_path(url):
    """https://shirodo.com/guide/kiroku/ -> guide/kiroku/index.html"""
    if not url.startswith(SITE_ROOT):
        raise ValueError(f"サイト外のURL: {url}")
    rel = url[len(SITE_ROOT):]
    if rel == "":
        return "index.html"
    if not rel.endswith("/"):
        return rel
    return rel + "index.html"


def git_last_commit_date(path):
    """そのファイルの最終コミット日（YYYY-MM-DD）。履歴がなければ None。"""
    out = subprocess.run(
        ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.strip()
    return out or None


def is_dirty(path):
    """未コミットの変更（ステージ済みを含む）があるか。"""
    out = subprocess.run(
        ["git", "status", "--porcelain", "--", path],
        cwd=REPO, capture_output=True, text=True,
    ).stdout.strip()
    return bool(out)


def resolve_lastmod(path, today):
    """このページの lastmod に入れるべき日付を返す。"""
    if is_dirty(path):
        return today
    return git_last_commit_date(path) or today


def sync(text, resolve):
    """sitemap本文の lastmod を差し替える。(新しい本文, 変更リスト, 警告リスト) を返す。"""
    changes, warnings = [], []

    def replace_block(m):
        block = m.group(0)
        loc = re.search(r"<loc>(.*?)</loc>", block).group(1)
        try:
            path = url_to_path(loc)
        except ValueError as e:
            warnings.append(str(e))
            return block
        if not (REPO / path).exists():
            warnings.append(f"sitemapにあるがファイルが無い: {loc} -> {path}")
            return block
        want = resolve(path)
        current = re.search(r"<lastmod>(.*?)</lastmod>", block)
        if not current:
            warnings.append(f"lastmodが無い: {loc}")
            return block
        if current.group(1) != want:
            changes.append((loc, current.group(1), want))
            block = block.replace(
                f"<lastmod>{current.group(1)}</lastmod>", f"<lastmod>{want}</lastmod>", 1
            )
        return block

    new_text = re.sub(r"<url>.*?</url>", replace_block, text, flags=re.S)
    return new_text, changes, warnings


def find_unlisted_pages(text):
    """sitemapに載っていない index.html を探す（新ページの追記漏れ検出）。"""
    listed = {url_to_path(u) for u in re.findall(r"<loc>(.*?)</loc>", text)}
    found = []
    for p in REPO.rglob("index.html"):
        rel = p.relative_to(REPO)
        if set(rel.parts) & IGNORED_DIRS:
            continue
        if any(part.startswith(".") for part in rel.parts):
            continue
        if str(rel) not in listed:
            found.append(str(rel))
    return sorted(found)


def main():
    check_only = "--check" in sys.argv
    today = date.today().isoformat()
    text = SITEMAP.read_text(encoding="utf-8")

    new_text, changes, warnings = sync(text, lambda p: resolve_lastmod(p, today))
    unlisted = find_unlisted_pages(text)

    for w in warnings:
        print(f"警告: {w}")
    for rel in unlisted:
        print(f"警告: sitemapに未掲載のページ: {rel}")

    if not changes:
        print("lastmod: 全て最新（変更なし）")
    else:
        for loc, old, new in changes:
            print(f"{'要更新' if check_only else '更新'}: {loc}  {old} -> {new}")

    if check_only:
        if changes or unlisted:
            print("\n--check: ズレを検出しました。`python3 scripts/update_sitemap.py` で同期してください。")
            return 1
        return 0

    if changes:
        SITEMAP.write_text(new_text, encoding="utf-8")
        print(f"\nOK: {SITEMAP} を更新（{len(changes)}件）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
