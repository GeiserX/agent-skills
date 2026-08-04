#!/usr/bin/env python3
"""Keep the sergio-loop Stop hook registered on every driver account.

WHY THIS EXISTS. Claude Code reads settings from `$CLAUDE_CONFIG_DIR`, which the driver points at a
PER-ACCOUNT directory. When the driver rotates accounts — for quota, or any other reason — the new
account's `settings.json` is a different file, and a Stop hook registered on the old one is simply
not there any more. The loop then stops advancing with no error, no log line and no failed check:
the hook is never invoked at all, so it cannot even report that it declined. `~/.claude/settings.json`
carrying the hook proves nothing, because the per-account file overrides it.

That failure cost an entire session of wrong diagnoses — cwd scoping, continuation budget, background
tasks — before the real cause turned out to be a rotation. It outranks every other silent stop,
because it disables the machinery that would have reported any of the others.

Repair is deliberately narrow. It only ever ADDS a missing `Stop` entry: never edits, reorders or
removes an existing one, never invents a settings file for an account that has none, and never
touches a file it could not parse. A settings file is the whole configuration of an account, so the
damage from writing one badly is far worse than the silence this fixes.
"""

from __future__ import annotations

import json
import os
import shutil
import time
from pathlib import Path
from typing import Any

# Overridable so tests never write the operator's real accounts — the same reason `pointer_path`
# honours the runtime-directory override. A test that repairs live configuration is not a test.
ACCOUNTS_DIRECTORY_ENV = "SERGIO_LOOP_ACCOUNTS_DIR"
DEFAULT_ACCOUNTS_DIRECTORY = "~/.config/neutral-driver/accounts"

HOOK_MARKER = "sergio-loop-stop-hook"
MAX_SETTINGS_BYTES = 1024 * 1024


def accounts_directory() -> Path:
    configured = os.environ.get(ACCOUNTS_DIRECTORY_ENV, DEFAULT_ACCOUNTS_DIRECTORY)
    return Path(os.path.abspath(os.path.expanduser(configured)))


def stop_entry() -> dict[str, Any]:
    """The canonical entry to add.

    Kept literal rather than copied from whichever account happens to be correct at the time, so the
    result does not depend on the state of a "reference" account. Paths are derived from the home
    directory rather than hardcoded, so the same code is testable off this machine.
    """
    hooks_directory = Path.home() / ".claude" / "hooks"
    return {
        "hooks": [
            {"type": "command", "command": f"{hooks_directory / 'notify-mac.sh'} stop"},
            {
                "type": "command",
                "command": f"python3 {hooks_directory / 'sergio-loop-stop-hook.py'}",
                "timeout": 10,
            },
        ]
    }


def has_hook(settings: object) -> bool:
    """Whether a parsed settings object already registers the Stop hook.

    Matches on the script NAME, not the whole command line, so an account whose entry differs in
    interpreter, flags or absolute path still counts as registered — re-adding a second copy would
    run the hook twice per turn-end and burn continuations in pairs.
    """
    if not isinstance(settings, dict):
        return False
    for group in settings.get("hooks", {}).get("Stop", []) or []:
        if not isinstance(group, dict):
            continue
        for hook in group.get("hooks", []) or []:
            if isinstance(hook, dict) and HOOK_MARKER in str(hook.get("command", "")):
                return True
    return False


def _read_settings(path: Path) -> dict[str, Any] | None:
    """Parsed settings, or None when the file is unreadable, oversized or not an object."""
    try:
        if path.stat().st_size > MAX_SETTINGS_BYTES:
            return None
        parsed = json.loads(path.read_text("utf-8"))
    except (OSError, ValueError):
        return None
    return parsed if isinstance(parsed, dict) else None


def audit(*, accounts: Path | None = None) -> tuple[list[str], list[str]]:
    """(registered, missing) account names. Read-only."""
    directory = accounts or accounts_directory()
    registered: list[str] = []
    missing: list[str] = []
    if not directory.is_dir():
        return registered, missing
    for account in sorted(p for p in directory.iterdir() if p.is_dir()):
        path = account / "settings.json"
        if not path.is_file():
            # An account with no settings file of its own is not ours to invent one for; a Codex
            # account legitimately has none.
            continue
        settings = _read_settings(path)
        if settings is None:
            continue  # unparseable is not "missing": repairing it would mean rewriting what we
            # could not read, and losing the account's configuration
        (registered if has_hook(settings) else missing).append(account.name)
    return registered, missing


def ensure_registration(*, accounts: Path | None = None) -> list[str]:
    """Add the Stop entry to any account missing it. Returns the accounts repaired.

    Never raises: this runs on the session-start path, where a failure must not stop a session from
    opening. A repair that does not happen costs continuation on the NEXT session; an exception here
    would cost the session in front of you.
    """
    directory = accounts or accounts_directory()
    repaired: list[str] = []
    _, missing = audit(accounts=directory)
    for name in missing:
        path = directory / name / "settings.json"
        settings = _read_settings(path)
        if settings is None or has_hook(settings):
            continue  # re-read: another session may have repaired it since the audit
        try:
            shutil.copy2(path, path.with_suffix(f".json.bak-{int(time.time())}"))
            settings.setdefault("hooks", {}).setdefault("Stop", []).append(stop_entry())
            temporary = path.with_suffix(".json.tmp")
            temporary.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
            temporary.replace(path)
        except (OSError, ValueError):
            continue
        repaired.append(name)
    return repaired
