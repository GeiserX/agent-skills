"""scripts/install.sh, run against a throwaway HOME."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALL = ROOT / "scripts" / "install.sh"


@unittest.skipUnless(shutil.which("bash"), "bash is required")
class InstallTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.home = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_install(self, *args: str) -> subprocess.CompletedProcess[str]:
        env = dict(os.environ, HOME=os.fspath(self.home))
        return subprocess.run(
            ["bash", os.fspath(INSTALL), *args],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_every_skill_links_into_skills(self) -> None:
        result = self.run_install()
        self.assertEqual(0, result.returncode, result.stderr)

        expected = sorted(p.name for p in (ROOT / "skills").iterdir() if (p / "SKILL.md").is_file())
        installed = self.home / ".claude" / "skills"
        self.assertEqual(expected, sorted(p.name for p in installed.iterdir()))
        for name in expected:
            link = installed / name
            self.assertTrue(link.is_symlink(), name)
            self.assertEqual((ROOT / "skills" / name).resolve(), link.resolve())

    def test_an_existing_destination_moves_to_the_backup_folder(self) -> None:
        installed = self.home / ".claude" / "skills"
        installed.mkdir(parents=True)
        (installed / "eli5").write_text("mine\n", encoding="utf-8")

        result = self.run_install("eli5")

        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual((ROOT / "skills" / "eli5").resolve(), (installed / "eli5").resolve())
        backups = list((self.home / ".claude" / "skills-backups").glob("*/eli5"))
        self.assertEqual(1, len(backups))
        self.assertEqual("mine\n", backups[0].read_text(encoding="utf-8"))

    def test_codex_links_into_codex_skills(self) -> None:
        result = self.run_install("--codex", "file-pr")

        self.assertEqual(0, result.returncode, result.stderr)
        link = self.home / ".agents" / "skills" / "file-pr"
        self.assertEqual((ROOT / "codex" / "skills" / "file-pr").resolve(), link.resolve())
        self.assertFalse((self.home / ".claude" / "skills").exists())

    def test_an_install_folder_that_is_the_source_is_refused(self) -> None:
        (self.home / ".claude").mkdir()
        (self.home / ".claude" / "skills").symlink_to(ROOT / "skills")

        result = self.run_install("eli5")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("refusing", result.stderr)
        self.assertTrue((ROOT / "skills" / "eli5" / "SKILL.md").is_file())

    def test_an_unknown_skill_fails(self) -> None:
        result = self.run_install("no-such-skill")

        self.assertNotEqual(0, result.returncode)
        self.assertIn("no such skill", result.stderr)


if __name__ == "__main__":
    unittest.main()
