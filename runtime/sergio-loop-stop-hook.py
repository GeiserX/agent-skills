#!/usr/bin/env python3
"""Global Claude Code Stop hook for repository-scoped Sergio loops."""

from __future__ import annotations

import json
import re
import sys
from typing import Any

from sergio_loop_state import discover_repository, tick


MAX_HOOK_INPUT_BYTES = 1024 * 1024
ALLOW_OUTPUT = '{"continue":true,"suppressOutput":true}'
ALLOW_REASON_PATTERN = re.compile(
    r"(?:"
    r"context(?:\s+window)?(?:\s+length)?(?:\s+(?:exceeded|limit))?"
    r"|token(?:s)?(?:\s+(?:exceeded|limit|maximum))"
    r"|\bauth(?:entication|orization)?(?:[\s_-]*(?:error|fail(?:ed|ure)?))?\b"
    r"|\bunauthorized\b|\bforbidden\b|\boauth(?:[\s_-]*(?:error|fail(?:ed|ure)?))?\b"
    r"|\b(?:401|403|429)\b"
    r"|rate[\s_-]*limit|too\s+many\s+requests"
    r")",
    re.IGNORECASE,
)
REASON_KEYS = {
    "error",
    "error_message",
    "reason",
    "status",
    "status_code",
    "stop_reason",
}


def _allow() -> None:
    sys.stdout.write(ALLOW_OUTPUT + "\n")


def _reason_text(payload: dict[str, Any]) -> str:
    values: list[str] = []
    for key, value in payload.items():
        if key.casefold() not in REASON_KEYS:
            continue
        if isinstance(value, (str, int, float)):
            values.append(str(value))
        elif isinstance(value, dict):
            values.extend(
                str(nested)
                for nested in value.values()
                if isinstance(nested, (str, int, float))
            )
    return "\n".join(values)


def _read_payload() -> dict[str, Any] | None:
    # SECURITY-REVIEW: hook stdin is untrusted and bounded before JSON parsing.
    raw = sys.stdin.buffer.read(MAX_HOOK_INPUT_BYTES + 1)
    if len(raw) > MAX_HOOK_INPUT_BYTES:
        return None
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def main() -> int:
    try:
        payload = _read_payload()
        if payload is None or ALLOW_REASON_PATTERN.search(_reason_text(payload)):
            _allow()
            return 0
        if payload.get("background_tasks") or payload.get("session_crons"):
            _allow()
            return 0
        cwd = payload.get("cwd")
        session_id = payload.get("session_id", payload.get("sessionId"))
        if (
            not isinstance(cwd, str)
            or not isinstance(session_id, str)
            or not session_id
        ):
            _allow()
            return 0
        repository = discover_repository(cwd)
        if repository is None:
            _allow()
            return 0
        should_block, prompt = tick(repository[0], repository[1], session_id)
        if not should_block or prompt is None:
            _allow()
            return 0
        sys.stdout.write(
            json.dumps(
                {"decision": "block", "reason": prompt},
                ensure_ascii=False,
                separators=(",", ":"),
            )
            + "\n"
        )
        return 0
    except Exception:
        # Global Stop hooks fail open on malformed, unsafe, or busy state.
        _allow()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
