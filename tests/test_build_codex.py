from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
import unittest
from pathlib import Path


REPO = Path(__file__).parents[1]
SCRIPT = REPO / "scripts" / "build_codex.py"
SPEC = importlib.util.spec_from_file_location("build_codex", SCRIPT)
assert SPEC and SPEC.loader
build_codex = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = build_codex
SPEC.loader.exec_module(build_codex)


class CodexMirrorTests(unittest.TestCase):
    def test_committed_codex_copies_match_a_fresh_build(self) -> None:
        problems = build_codex.check(REPO / "skills", REPO / "codex" / "skills")
        self.assertEqual(problems, [], "run: python3 scripts/build_codex.py")

    def test_every_canonical_skill_has_a_codex_copy_with_the_explicit_only_policy(self) -> None:
        for skill in (REPO / "skills").iterdir():
            if not (skill / "SKILL.md").is_file():
                continue
            codex = REPO / "codex" / "skills" / skill.name
            self.assertIn("## Running in Codex", (codex / "SKILL.md").read_text())
            self.assertNotIn("disable-model-invocation", (codex / "SKILL.md").read_text())
            self.assertEqual((codex / "agents" / "openai.yaml").read_text(), build_codex.POLICY)

    def test_check_fails_when_a_canonical_skill_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills, codex = Path(tmp) / "skills", Path(tmp) / "codex"
            shutil.copytree(REPO / "skills", skills)
            build_codex.build(skills, codex)
            self.assertEqual(build_codex.check(skills, codex), [])
            skill_md = skills / "research" / "SKILL.md"
            skill_md.write_text(skill_md.read_text() + "\nOne more rule.\n")
            self.assertEqual(build_codex.check(skills, codex), ["differs: research/SKILL.md"])

    def test_check_fails_when_a_skill_has_no_codex_copy(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills, codex = Path(tmp) / "skills", Path(tmp) / "codex"
            shutil.copytree(REPO / "skills", skills)
            build_codex.build(skills, codex)
            shutil.copytree(skills / "research", skills / "research-two")
            self.assertEqual(build_codex.check(skills, codex), ["missing in codex/skills: research-two"])


if __name__ == "__main__":
    unittest.main()
