"""コミット前の関所（.githooks/pre-commit）と、それを飛ばすコマンドを止めるClaude Codeフックのテスト。"""
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import precommit_generated  # noqa: E402

_spec = importlib.util.spec_from_file_location("block_hook_bypass", ROOT / ".claude" / "hooks" / "block_hook_bypass.py")
bypass = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bypass)


class RelevantPathTest(unittest.TestCase):
    def test_generated_pages_and_sources_are_checked(self):
        for p in ["100meijo/index.html", "guide/level/index.html", "data/level.json",
                  "scripts/gen_100meijo.py", "scripts/gen_level.py", "scripts/gen_common.py"]:
            with self.subTest(path=p):
                self.assertTrue(precommit_generated.is_relevant(p))

    def test_other_commits_pass_through(self):
        # 日次メトリクスの自動コミットなどを巻き込まない
        for p in ["metrics/DAILY.md", "index.html", "guide/mochimono/index.html", "sitemap.xml", "CLAUDE.md"]:
            with self.subTest(path=p):
                self.assertFalse(precommit_generated.is_relevant(p))


class BypassDetectionTest(unittest.TestCase):
    BLOCKED = [
        'git commit --no-verify -m "x"',
        "git commit -n -m x",
        "git commit -anm x",
        "git -C /repo commit --no-verify",
        "git -c core.hooksPath=/dev/null commit -m x",
        "git config core.hooksPath /tmp/none",
        "git config --unset core.hooksPath",
        "echo a\ngit status\ngit commit -n -m y",
        "git add a && git commit --no-verify -m z",
    ]
    ALLOWED = [
        'git commit -m "x"',
        'git commit -am "use -n flag docs"',
        'git commit -m "--no-verify を禁止"',
        "git commit -q -F - <<'MSG'\nfeat: --no-verify を止める\n-n も\nMSG",
        "git commit -q -F - <<'MSG' && git log --oneline -1\nbody -n\nMSG",
        "git config core.hooksPath .githooks",
        "git config --get core.hooksPath",
        "git log -n 3 && git commit -m x",
        "git commit -m x\ngit log --oneline -n 3",
        "head -n 5 file",
        'git commit -m "unbalanced',
        'git commit -m "line1\nline2 -n"',
    ]

    def test_blocks_hook_bypass(self):
        for cmd in self.BLOCKED:
            with self.subTest(cmd=cmd):
                self.assertIsNotNone(bypass.find_bypass(cmd))

    def test_allows_normal_commands(self):
        for cmd in self.ALLOWED:
            with self.subTest(cmd=cmd):
                self.assertIsNone(bypass.find_bypass(cmd))


class HookWiringTest(unittest.TestCase):
    def test_pre_commit_calls_generated_check(self):
        hook = (ROOT / ".githooks" / "pre-commit").read_text(encoding="utf-8")
        self.assertIn("scripts/precommit_generated.py", hook)


if __name__ == "__main__":
    unittest.main()
