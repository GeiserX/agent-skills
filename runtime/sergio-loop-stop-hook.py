#!/usr/bin/env python3
"""Global Claude Code Stop hook for repository-scoped Sergio loops."""

from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path
from typing import Any

from sergio_loop_state import discover_repository, pointer_path, tick


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


DEBUG_PATH = Path.home() / ".claude" / "sergio-loop-hook-debug.jsonl"


def _trace(stage: str, payload: object = None) -> None:
    """Record every decision — WHY a stop was allowed, and that a grant happened — so a silent
    no-continue is diagnosable after the fact and a grant is a fact in the log, not an inference
    from the slot counter.

    A hook that fails open leaves no trace by construction: the loop simply stops and every piece of
    state still looks healthy, which has now cost several wrong diagnoses. Probing the hook by hand
    is worse than useless — each block consumes one of the finite continuations the loop needs, so
    the measurement destroys what it measures.

    Records SHAPE only: the stage that returned, the payload's top-level key names, and the type and
    first-entry keys of the task lists. Never a value, so no prompt text, path content or credential
    can reach this file.
    """
    try:
        record: dict[str, Any] = {"at": time.time(), "stage": stage}
        if isinstance(payload, dict):
            record["keys"] = sorted(payload)[:40]
            # The two values that decide ownership. `tick` declines silently when either disagrees
            # with the armed loop, and that decline is indistinguishable from every other allow.
            # A cwd is a path and a session id is a UUID — neither is a secret, and without them a
            # mismatch cannot be told apart from a healthy loop.
            record["cwd"] = payload.get("cwd")
            record["payload_session"] = payload.get("session_id", payload.get("sessionId"))
            for field in ("background_tasks", "session_crons"):
                value = payload.get(field)
                if value is None:
                    continue
                entry = value[0] if isinstance(value, (list, tuple)) and value else None
                record[field] = {
                    "type": type(value).__name__,
                    "len": len(value) if isinstance(value, (list, tuple)) else None,
                    "entry_keys": sorted(entry)[:20] if isinstance(entry, dict) else None,
                    # Status VALUES are a small enum, never free text, so recording them is safe and
                    # is the only way to tell genuinely-running work from work merely still listed.
                    "statuses": [
                        e.get("status", e.get("state"))
                        for e in value[:12]
                        if isinstance(e, dict)
                    ]
                    if isinstance(value, (list, tuple))
                    else None,
                    # The classifier's verdict, recorded rather than acted on. The gate that used it
                    # is gone (see main), but a trace that says "the payload still listed work, and
                    # none of it was live" is what distinguishes a phantom task from a real one when
                    # a future stop needs explaining.
                    "live": _has_live_work(value),
                }
        with open(
            os.open(DEBUG_PATH, os.O_WRONLY | os.O_CREAT | os.O_APPEND | os.O_NOFOLLOW, 0o600), "a"
        ) as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
    except Exception:
        pass  # diagnostics must never change the hook's decision


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


RUNNING_STATES = {
    "active",
    "in_progress",
    "pending",
    "queued",
    "running",
    "started",
    "starting",
    "working",
}

def _has_live_work(entries: object) -> bool:
    """Whether background work is STILL RUNNING, rather than merely listed.

    Yielding the stop while real work runs is correct — the loop should not talk over a live build.
    But the payload lists a task after it FINISHES too, and treating mere presence as "busy" made a
    single backgrounded command disable continuation for the rest of the session: every later
    turn-end saw a non-empty list, allowed the stop, and the loop advanced only when a human typed.
    That is silent, and it looks exactly like the hook not being installed.

    Work counts as live only when a status SAYS it is running. That direction is deliberate. The
    first attempt blacklisted finished states, so any status string the list did not anticipate read
    as "still running" and stopped the loop — permanently, because a finished task stays listed. The
    two failure modes are not symmetric: mistaking finished work for live work silently ends the
    loop and needs a human to notice, while mistaking live work for finished work merely lets the
    loop continue alongside it, which is what foregrounding long work already assumes.
    """
    if not entries:
        return False
    if not isinstance(entries, (list, tuple)):
        return False  # an unrecognized shape says nothing about liveness
    for entry in entries:
        if not isinstance(entry, dict):
            continue
        status = entry.get("status", entry.get("state"))
        if isinstance(status, str) and status.strip().casefold() in RUNNING_STATES:
            return True
    return False


def _is_inside(inner: Path, outer: Path) -> bool:
    """Whether `inner` lies within `outer` — used to keep a binding from reaching DOWN into a nest.

    A repository checked out inside another is governed by the NEAREST one; a session working there
    must never be driven by the enclosing repository's loop. The binding fallback would otherwise
    reintroduce exactly that, because the enclosing repository is a perfectly ordinary thing for a
    session to have bound earlier. Sibling repositories under a shared parent are unaffected, which
    is the case the fallback exists to serve.
    """
    try:
        inner.relative_to(outer)
    except ValueError:
        return False
    return True


def _pointed_repository(session_id: str) -> tuple[Path, Path] | None:
    """The repository a session explicitly bound its loop to.

    A Stop payload carries the session's cwd, and the loop is discovered from it. When that cwd is
    not inside a git repository — a session opened at a workspace parent that merely CONTAINS the
    repositories, which is ordinary — discovery finds nothing and the loop can never continue, no
    matter how much live state it has. This consults an explicit, per-session binding written by the
    workflow itself.

    Deliberately NOT a scan of the state store: the entry must name this exact session, so a loop
    belonging to another session is still never continued here. The path is re-canonicalized through
    the same routine as any other repository, so a bogus or stale pointer resolves to nothing rather
    than to something unexpected, and every later gate (identity, expiry, budget) still applies.
    """
    try:
        path = pointer_path()
        if not path.is_file() or path.is_symlink():
            return None
        entries = json.loads(path.read_text("utf-8"))
        target = entries.get(session_id) if isinstance(entries, dict) else None
        if not isinstance(target, str) or not target:
            return None
        return discover_repository(target)
    except (OSError, ValueError):
        return None


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
            _trace("allow:unparseable-or-reason-pattern", payload)
            _allow()
            return 0
        # NO background-work gate. Deliberately removed, after it ended this loop three separate
        # times while every piece of state still read healthy.
        #
        # Its purpose was politeness — don't continue while a build is running — never correctness.
        # But the payload keeps listing a task after it finishes, and a task the runtime never reaps
        # keeps reporting "running" with no process behind it. Either way the gate latches: one
        # entry, and the loop yields at every turn-end for the rest of the session, advancing only
        # when a human notices and types. Both a presence check and a status check were tried and
        # both latched.
        #
        # The asymmetry decides it. Continuing beside a live background task costs some interleaved
        # output. Yielding to a phantom one costs the entire loop, silently, with no signal anyone
        # can act on. `_trace` still records every other allow-path, so a future silent stop names
        # its own cause instead of costing another round of guessing.
        cwd = payload.get("cwd")
        session_id = payload.get("session_id", payload.get("sessionId"))
        if (
            not isinstance(cwd, str)
            or not isinstance(session_id, str)
            or not session_id
        ):
            _trace("allow:missing-cwd-or-session", payload)
            _allow()
            return 0
        repository = discover_repository(cwd)
        if repository is None:
            repository = _pointed_repository(session_id)
        if repository is None:
            _trace("allow:no-repository-resolved", payload)
            _allow()
            return 0
        should_block, prompt = tick(repository[0], repository[1], session_id)
        if not should_block:
            # The cwd DID resolve to a repository, but its loop is not ours — a sibling session owns
            # the loop there, or that repository has none. Discovery succeeding is therefore not
            # enough: a session that explicitly bound its loop to another repository would never
            # continue, because the pointer above is only consulted when discovery finds nothing.
            # This is the ordinary shape of a shared workspace — several sessions, one repository
            # parent, one loop slot per repository — and it fails silently, exactly like an
            # uninstalled hook.
            #
            # Strictly additive: a session with no pointer entry is unaffected, a pointer naming the
            # repository already ticked is skipped, and every gate inside `tick` (ownership, expiry,
            # iteration budget) still applies to the second call. A loop owned by another session is
            # still never continued.
            pointed = _pointed_repository(session_id)
            if (
                pointed is not None
                and pointed[0] != repository[0]
                and not _is_inside(repository[0], pointed[0])
            ):
                should_block, prompt = tick(pointed[0], pointed[1], session_id)
        if not should_block or prompt is None:
            _trace("allow:tick-declined", payload)
            _allow()
            return 0
        # Grants are traced too. They used to leave no trace by construction — _trace ran only on allow
        # paths — so "did the hook grant here?" was answerable only by inference from the slot counter,
        # which has already cost wrong diagnoses. Same shape-only record as every other row: stage, key
        # names, cwd, session id. Never the prompt text.
        _trace("block:granted", payload)
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
        _trace("allow:exception")
        _allow()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
