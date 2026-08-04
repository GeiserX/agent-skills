#!/usr/bin/env python3
"""Report — and optionally repair — sergio-loop Stop-hook registration across driver accounts.

The repair itself runs automatically from the SessionStart hook; this is the manual and CI-shaped
face of the same routine, for answering "is every account armed?" without opening a session.

    ensure-sergio-loop-hook-on-all-accounts.py            # repair anything missing
    ensure-sergio-loop-hook-on-all-accounts.py --check    # report only; non-zero if any is missing

`--check` writes nothing and exits non-zero when an account lacks the hook, so it can gate a driver
command or a shell profile. See sergio_loop_registration for why a missing registration outranks
every other cause of a silently dead loop.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from sergio_loop_registration import (  # noqa: E402
    accounts_directory,
    audit,
    ensure_registration,
)


def main(argv: list[str] | None = None) -> int:
    arguments = sys.argv[1:] if argv is None else argv
    check_only = "--check" in arguments

    directory = accounts_directory()
    if not directory.is_dir():
        print(f"no accounts directory at {directory}")
        return 0

    registered, missing = audit()
    for name in registered:
        print(f"ok    {name}")

    if check_only:
        for name in missing:
            print(f"MISS  {name}")
        if missing:
            print(f"\n{len(missing)} account(s) missing the hook: {', '.join(missing)}")
            return 1
        print("\nall accounts carry the sergio-loop Stop hook")
        return 0

    for name in ensure_registration():
        print(f"ADDED {name}")
    print("\nall accounts carry the sergio-loop Stop hook")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
