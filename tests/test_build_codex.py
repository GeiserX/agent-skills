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

    def _built(self, tmp: str) -> tuple[Path, Path]:
        skills, codex = Path(tmp) / "skills", Path(tmp) / "codex"
        shutil.copytree(REPO / "skills", skills)
        build_codex.build(skills, codex)
        return skills, codex

    def test_check_fails_when_a_codex_file_changes_type(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills, codex = self._built(tmp)
            target = codex / "research" / "SKILL.md"
            content = target.read_bytes()
            target.unlink()
            target.mkdir()
            self.assertEqual(build_codex.check(skills, codex), ["differs: research/SKILL.md"])
            target.rmdir()
            elsewhere = Path(tmp) / "same-bytes.md"
            elsewhere.write_bytes(content)
            target.symlink_to(elsewhere)
            self.assertEqual(build_codex.check(skills, codex), ["differs: research/SKILL.md"])
            target.unlink()
            target.symlink_to("/nonexistent/target")
            self.assertEqual(build_codex.check(skills, codex), ["differs: research/SKILL.md"])

    def test_check_fails_when_the_executable_bit_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            skills, codex = self._built(tmp)
            (codex / "research" / "SKILL.md").chmod(0o755)
            self.assertEqual(build_codex.check(skills, codex), ["differs: research/SKILL.md"])

    def test_a_relative_symlink_in_a_skill_ships_as_its_content(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(REPO / "skills" / "research", root / "skills" / "research")
            (root / "shared").mkdir()
            (root / "shared" / "note.md").write_text("shared note\n")
            (root / "skills" / "research" / "note.md").symlink_to("../../shared/note.md")
            build_codex.build(root / "skills", root / "codex" / "skills")
            copy = root / "codex" / "skills" / "research" / "note.md"
            self.assertFalse(copy.is_symlink())
            self.assertEqual(copy.read_text(), "shared note\n")

    def test_unclosed_frontmatter_is_a_clear_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "no closing ---"):
            build_codex.codex_skill_md("---\nname: x\ndescription: y\n\n# Title\n")


if __name__ == "__main__":
    unittest.main()
