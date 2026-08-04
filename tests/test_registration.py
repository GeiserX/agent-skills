"""Stop-hook registration across driver accounts.

A rotated-to account whose settings.json lacks the Stop hook cannot report anything — not even that
it declined — so this repair outranks every other cause of a silently dead loop. It is also the one
piece of the loop that writes a file it does not own, so most of what is pinned here is what it must
NOT do.
"""

from __future__ import annotations

import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
SPEC = importlib.util.spec_from_file_location(
    "sergio_loop_registration", ROOT / "runtime" / "sergio_loop_registration.py"
)
assert SPEC and SPEC.loader
registration = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(registration)


class RegistrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.accounts = Path(self.temporary.name)
        self.previous = os.environ.get(registration.ACCOUNTS_DIRECTORY_ENV)
        os.environ[registration.ACCOUNTS_DIRECTORY_ENV] = os.fspath(self.accounts)

    def tearDown(self) -> None:
        if self.previous is None:
            os.environ.pop(registration.ACCOUNTS_DIRECTORY_ENV, None)
        else:
            os.environ[registration.ACCOUNTS_DIRECTORY_ENV] = self.previous
        self.temporary.cleanup()

    def make_account(self, name: str, settings: object | None) -> Path:
        account = self.accounts / name
        account.mkdir(parents=True)
        path = account / "settings.json"
        if settings is not None:
            path.write_text(
                settings if isinstance(settings, str) else json.dumps(settings),
                encoding="utf-8",
            )
        return path

    def read(self, name: str) -> dict:
        return json.loads((self.accounts / name / "settings.json").read_text(encoding="utf-8"))

    def test_an_account_missing_the_hook_is_repaired(self) -> None:
        self.make_account("rotated", {"model": "opus"})

        self.assertEqual(["rotated"], registration.ensure_registration())

        self.assertTrue(registration.has_hook(self.read("rotated")))
        self.assertEqual("opus", self.read("rotated")["model"], "unrelated settings must survive")

    def test_repair_is_idempotent_and_never_registers_the_hook_twice(self) -> None:
        """A second entry would run the hook twice per turn-end, burning continuations in pairs."""
        self.make_account("rotated", {})
        registration.ensure_registration()

        self.assertEqual([], registration.ensure_registration(), "second run must be a no-op")

        commands = [
            hook.get("command", "")
            for group in self.read("rotated")["hooks"]["Stop"]
            for hook in group["hooks"]
        ]
        self.assertEqual(
            1, sum(registration.HOOK_MARKER in command for command in commands)
        )

    def test_an_existing_entry_is_never_edited_reordered_or_removed(self) -> None:
        existing = {
            "hooks": {
                "Stop": [{"hooks": [{"type": "command", "command": "/opt/notify.sh stop"}]}],
                "Notification": [{"hooks": [{"type": "command", "command": "/opt/n.sh"}]}],
            }
        }
        self.make_account("rotated", existing)

        registration.ensure_registration()

        after = self.read("rotated")
        self.assertEqual(
            existing["hooks"]["Stop"][0], after["hooks"]["Stop"][0], "existing entry must be intact"
        )
        self.assertEqual(existing["hooks"]["Notification"], after["hooks"]["Notification"])
        self.assertTrue(registration.has_hook(after))

    def test_a_differently_spelled_command_still_counts_as_registered(self) -> None:
        """Matching the whole command line would add a duplicate for any account whose entry differs
        in interpreter, flags or path."""
        self.make_account(
            "rotated",
            {
                "hooks": {
                    "Stop": [
                        {
                            "hooks": [
                                {
                                    "type": "command",
                                    "command": "/usr/bin/python3.12 /elsewhere/sergio-loop-stop-hook.py --v",
                                }
                            ]
                        }
                    ]
                }
            },
        )

        self.assertEqual([], registration.ensure_registration())

    def test_an_account_without_a_settings_file_is_left_alone(self) -> None:
        """A Codex account legitimately has none; inventing one is not this routine's business."""
        account = self.accounts / "cx-codex"
        account.mkdir()

        self.assertEqual([], registration.ensure_registration())

        self.assertFalse((account / "settings.json").exists())

    def test_unparseable_settings_are_never_rewritten(self) -> None:
        """Repairing what could not be read means replacing an account's whole configuration."""
        self.make_account("broken", "{ this is not json")

        self.assertEqual([], registration.ensure_registration())

        self.assertEqual(
            "{ this is not json",
            (self.accounts / "broken" / "settings.json").read_text(encoding="utf-8"),
        )

    def test_the_original_is_backed_up_before_a_write(self) -> None:
        self.make_account("rotated", {"model": "opus"})

        registration.ensure_registration()

        backups = list((self.accounts / "rotated").glob("settings.json.bak-*"))
        self.assertEqual(1, len(backups), "exactly one backup of the pre-repair file")
        self.assertEqual({"model": "opus"}, json.loads(backups[0].read_text(encoding="utf-8")))

    def test_audit_reports_without_writing(self) -> None:
        self.make_account("armed", {})
        registration.ensure_registration()
        self.make_account("bare", {})

        registered, missing = registration.audit()

        self.assertEqual(["armed"], registered)
        self.assertEqual(["bare"], missing)
        self.assertFalse(registration.has_hook(self.read("bare")), "audit must not repair")

    def test_a_missing_accounts_directory_is_not_an_error(self) -> None:
        os.environ[registration.ACCOUNTS_DIRECTORY_ENV] = os.fspath(self.accounts / "absent")

        self.assertEqual([], registration.ensure_registration())
        self.assertEqual(([], []), registration.audit())


if __name__ == "__main__":
    unittest.main()
