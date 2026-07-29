#!/usr/bin/env python3
"""Expose the current Claude session ID to subsequent shell commands."""

from __future__ import annotations

import json
import os
import shlex
import stat
import sys
from pathlib import Path
from typing import Any

from sergio_loop_state import StateError, validate_session_id


MAX_HOOK_INPUT_BYTES = 1024 * 1024
MAX_ENV_FILE_BYTES = 1024 * 1024


def _read_payload() -> dict[str, Any] | None:
    # SECURITY-REVIEW: SessionStart stdin is untrusted and bounded before parsing.
    raw = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
    if len(raw) > MAX_HOOK_INPUT_BYTES:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _append_export(path_value: str, session_id: str) -> None:
    # SECURITY-REVIEW: CLAUDE_ENV_FILE is environment-controlled. The final
    # component is opened no-follow, verified regular/user-owned, and bounded.
    path = Path(os.path.abspath(os.path.expanduser(path_value)))
    flags = os.O_WRONLY | os.O_APPEND | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid():
            raise StateError("unsafe CLAUDE_ENV_FILE")
        line = (
            f"export SERGIO_CLAUDE_SESSION_ID={shlex.quote(session_id)}\n"
        ).encode("utf-8")
        if metadata.st_size + len(line) > MAX_ENV_FILE_BYTES:
            raise StateError("CLAUDE_ENV_FILE is too large")
        written = os.write(descriptor, line)
        if written != len(line):
            raise StateError("short CLAUDE_ENV_FILE write")
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def main() -> int:
    try:
        payload = _read_payload()
        env_file = os.environ.get("CLAUDE_ENV_FILE")
        if payload is None or not env_file:
            return 0
        session_id = payload.get("session_id", payload.get("sessionId"))
        _append_export(env_file, validate_session_id(session_id))
    except Exception:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
