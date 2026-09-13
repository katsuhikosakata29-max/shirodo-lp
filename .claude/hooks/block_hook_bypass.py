#!/usr/bin/env python3
"""Claude Code の PreToolUse(Bash) フック: Gitのコミット前フックを飛ばすコマンドを止める。

止めるもの:
- git commit の --no-verify / -n（-an のような短縮オプションの束も含む）
- git -c core.hooksPath=... での一時上書き
- git config での core.hooksPath の変更・解除（.githooks への設定は許可）

止めたら終了コード2と理由（stderr）を返す。解析できないコマンドは通す
（本当の関所は .githooks/pre-commit で、ここは飛ばし防止の補助）。
"""
import json
import re
import shlex
import sys

ALLOWED_HOOKS_PATH = ".githooks"
# 値を取るオプション（次のトークンはメッセージ等なので検査しない）
COMMIT_OPTS_WITH_VALUE = {"-m", "-F", "-C", "-c", "-t", "--author", "--date", "--message", "--file",
                          "--template", "--reuse-message", "--reedit-message", "--fixup", "--squash",
                          "--cleanup", "--trailer", "--pathspec-from-file"}
GIT_GLOBAL_OPTS_WITH_VALUE = {"-C", "-c", "--git-dir", "--work-tree", "--namespace"}
_HEREDOC = re.compile(r"<<-?\s*(['\"]?)(\w+)\1[^\n]*\n.*?\n\s*\2\s*(?:\n|$)", re.S)
_SEPARATORS = {"&&", "||", ";", "|", "&", "(", ")", ";;"}
_NEWLINE_RUN = re.compile(r"^[\n();<>|&]+$")


def _segments(command: str):
    """ヒアドキュメント本文（コミットメッセージ等）を除き、&& ; | で区切ったトークン列に分ける。"""
    body = _HEREDOC.sub("\n", command)
    # 改行も区切りとして扱う（引用符の中の改行はメッセージの一部なので区切らない）
    lex = shlex.shlex(body, posix=True, punctuation_chars="();<>|&\n")
    lex.whitespace = " \t\r"
    lex.whitespace_split = True
    seg = []
    for tok in lex:
        if tok in _SEPARATORS or _NEWLINE_RUN.match(tok):
            if seg:
                yield seg
            seg = []
        else:
            seg.append(tok)
    if seg:
        yield seg


def _bypass_in_segment(tokens):
    if "git" not in tokens:
        return None
    i = tokens.index("git") + 1
    # git のグローバルオプション
    while i < len(tokens) and tokens[i].startswith("-"):
        opt = tokens[i]
        if opt == "-c" and i + 1 < len(tokens) and tokens[i + 1].lower().startswith("core.hookspath"):
            return "git -c core.hooksPath=... でコミット前フックを差し替えようとしています"
        if opt.lower().startswith("-ccore.hookspath") or opt.lower().startswith("--config-env"):
            return "git の設定上書きでコミット前フックを差し替えようとしています"
        i += 2 if opt in GIT_GLOBAL_OPTS_WITH_VALUE else 1
    if i >= len(tokens):
        return None
    sub, args = tokens[i], tokens[i + 1:]

    if sub == "commit":
        j = 0
        while j < len(args):
            a = args[j]
            if a == "--":
                break
            if a == "--no-verify":
                return "git commit --no-verify でコミット前フックを飛ばそうとしています"
            if a in COMMIT_OPTS_WITH_VALUE:
                j += 2
                continue
            if re.fullmatch(r"-[A-Za-z]+", a):
                # -m / -F などの値付きオプションが束の途中にあれば、その後ろは値
                for ch in a[1:]:
                    if ch == "n":
                        return "git commit -n（--no-verify）でコミット前フックを飛ばそうとしています"
                    if f"-{ch}" in COMMIT_OPTS_WITH_VALUE:
                        break
            j += 1

    if sub == "config":
        lowered = [a.lower() for a in args]
        if "core.hookspath" in lowered:
            k = lowered.index("core.hookspath")
            if "--unset" in lowered or "--unset-all" in lowered:
                return "core.hooksPath を解除しようとしています（コミット前フックが無効になります）"
            value = args[k + 1] if k + 1 < len(args) else None
            if value is not None and value.rstrip("/") != ALLOWED_HOOKS_PATH:
                return f"core.hooksPath を {value} に変えようとしています（コミット前フックが無効になります）"
    return None


def find_bypass(command: str):
    try:
        for seg in _segments(command):
            reason = _bypass_in_segment(seg)
            if reason:
                return reason
    except ValueError:
        return None  # 引用符の不整合など、解析できないものは通す
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    command = (payload.get("tool_input") or {}).get("command") or ""
    reason = find_bypass(command)
    if reason:
        print(f"ブロック: {reason}。このリポジトリでは、生成ページの直接編集を止めるコミット前フックを飛ばせません。"
              "フックが失敗した場合は、原因（生成ページのズレ）をスクリプト側で直してからコミットしてください。",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
