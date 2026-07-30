#!/usr/bin/env python3
"""sergio-loop-why — answer "why did my loop stop?" in one command.

The loop's failure mode is silence. When a Stop is allowed instead of blocked, the hook writes
{"continue":true,"suppressOutput":true} and nothing else happens: the loop simply stops advancing and
looks exactly like the assistant deciding it was finished. Diagnosing that by hand needs four separate
checks — is the hook bound, does this account carry it, does my cwd resolve to the repository I think,
and do I still own the slot — and it has now cost two different agents a session each.

Worse, probing it interactively is self-defeating: every block spends one of the eight finite
continuations, so measuring the loop consumes the thing being measured. This reads state only. It never
arms, never stops, never writes, and never spends a continuation.

Usage:
    sergio-loop-why.py [--repo PATH] [--session-id ID] [--json]

Defaults: --repo from $PWD, --session-id from $SERGIO_CLAUDE_SESSION_ID or $CLAUDE_CODE_SESSION_ID.
Exit codes: 0 = this session owns a live loop; 1 = it does not (with the reason on stdout).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sergio_loop_state import (  # noqa: E402
    discover_repository,
    ownership_status,
    runtime_directory,
)

POINTER = Path.home() / ".claude" / "sergio-loop-session-repo.json"
TRACE = Path.home() / ".claude" / "sergio-loop-hook-debug.jsonl"

# What each state means and what to actually DO about it. The original failures were not caused by a
# lack of data but by nobody knowing which of several healthy-looking things was untrue, so every state
# names its own remedy.
ADVICE = {
    "ok": "This session owns a live loop. Stops will be blocked until the budget runs out.",
    "none": ("No loop is armed for this repository. If you expected one, it was never started "
             "(or it already terminated and was swept) — re-arm with `sergio_loop_state.py start`."),
    "owned-by-other": ("ANOTHER SESSION OWNS THIS REPOSITORY'S LOOP. Your stops are being allowed "
                       "silently — this is the failure that looks identical to a missing hook. Either "
                       "that lane is live (leave it alone and work in your own repository), or it was "
                       "abandoned and its claim expires on its own; only then can you re-arm."),
    "inactive": ("The slot exists but is finished or expired. Re-arm it if there is still work "
                 "(terminal_reason tells you how the previous run ended)."),
    "capped": ("You own the slot but have spent all continuations. This is normal: Claude Code "
               "overrides Stop hooks after 8 consecutive blocks. Re-arm to get a fresh budget."),
    "unknown": "Slot state is unreadable or torn. Inspect the JSON in the runtime directory by hand.",
}


def _pointer_for(session_id):
    try:
        return json.loads(POINTER.read_text("utf-8")).get(session_id)
    except Exception:
        return None


def _last_trace(session_id, limit=400):
    """Most recent hook decision recorded for this session, if the trace exists."""
    try:
        lines = TRACE.read_text("utf-8", errors="replace").splitlines()[-limit:]
    except Exception:
        return None
    for line in reversed(lines):
        try:
            rec = json.loads(line)
        except Exception:
            continue
        if rec.get("payload_session") == session_id:
            return rec
    return None


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--repo", default=os.getcwd())
    ap.add_argument("--session-id", default=os.environ.get("SERGIO_CLAUDE_SESSION_ID")
                    or os.environ.get("CLAUDE_CODE_SESSION_ID") or "")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)

    session_id = args.session_id
    discovered = discover_repository(args.repo)
    pointed = _pointer_for(session_id) if session_id else None

    # Report BOTH resolutions. "my cwd resolves to a repository I did not expect" is one of the two
    # ways this silently breaks, and it is invisible unless the resolved root is printed next to cwd.
    repo = discovered[0] if discovered else None
    if repo is None and pointed:
        p = discover_repository(pointed)
        repo = p[0] if p else None

    status = (ownership_status(repo, session_id) if (repo and session_id)
              else {"state": "unknown", "owner": None, "iteration": None,
                    "max_iterations": None, "terminal_reason": None})
    trace = _last_trace(session_id) if session_id else None

    out = {
        "cwd": args.repo,
        "resolvedRepository": str(repo) if repo else None,
        "resolvedVia": ("cwd" if discovered else ("pointer" if pointed else None)),
        "pointerEntry": pointed,
        "sessionId": session_id or None,
        "slot": status,
        "lastHookDecision": ({"stage": trace.get("stage"),
                              "at": trace.get("at"),
                              "cwd": trace.get("cwd")} if trace else None),
        "runtimeDirectory": str(runtime_directory(create=False)),
        "advice": ADVICE.get(status.get("state"), ""),
    }
    if args.json:
        print(json.dumps(out, indent=2))
        return 0 if status.get("state") == "ok" else 1

    print(f"cwd            : {out['cwd']}")
    print(f"repository     : {out['resolvedRepository']}  (resolved via {out['resolvedVia']})")
    if pointed and discovered and str(discovered[0]) != str(pointed):
        # Both exist and disagree — the shape that sends two lanes at one slot.
        print(f"  ^ NOTE: your pointer names a DIFFERENT repository: {pointed}")
    print(f"session        : {out['sessionId']}")
    owner = status.get("owner")
    same = owner == session_id if owner else None
    print(f"slot state     : {status.get('state')}")
    print(f"slot owner     : {owner}{'  (you)' if same else '  (NOT you)' if owner else ''}")
    if status.get("max_iterations") is not None:
        print(f"continuations  : {status.get('iteration')}/{status.get('max_iterations')}")
    if status.get("terminal_reason"):
        print(f"terminal reason: {status.get('terminal_reason')}")
    if trace:
        age = (time.time() - (trace.get("at") or 0)) / 60.0
        print(f"last stop      : {trace.get('stage')}  ({age:.0f}m ago, cwd={trace.get('cwd')})")
    print()
    print(out["advice"])
    return 0 if status.get("state") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
