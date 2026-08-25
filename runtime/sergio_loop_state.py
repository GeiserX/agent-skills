#!/usr/bin/env python3
"""Secure global state for repository-scoped Sergio loop Stop hooks."""

from __future__ import annotations

import argparse
import contextlib
import errno
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import subprocess
import sys
import time
import uuid
from collections.abc import Iterator
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
RUNTIME_DIRECTORY_ENV = "SERGIO_LOOP_RUNTIME_DIR"
DEFAULT_RUNTIME_DIRECTORY = "~/.claude/sergio-loop-runtime"
MAX_PROMPT_BYTES = 64 * 1024
MAX_STATE_BYTES = 128 * 1024
# Session→repository bindings (see pointer_path). One entry per armed session; bounded so a
# long-lived home directory cannot grow the file without limit.
POINTER_FILENAME = "sergio-loop-session-repo.json"
MAX_POINTER_ENTRIES = 64
MAX_REASON_BYTES = 4 * 1024
MAX_SESSION_ID_BYTES = 256
MAX_GIT_FILE_BYTES = 4 * 1024
MAX_EXPIRY_SECONDS = 7 * 24 * 60 * 60
# The loop's whole ceiling: 8 originally, 100 on 2026-08-13, 1000 on 2026-08-17 ("from 100 to
# 1000 by default"). Every other cap derives from this constant — DEFAULT_MAX_ITERATIONS,
# MAX_ITERATIONS, the clamp in `start`, and the re-clamp applied to existing state on normalize —
# so this one line is the only place to change it.
#
# Two things it does NOT govern, and both have ended runs that still had iterations to spare:
#   - the expiry (`--expires-in`, 6h by default, capped by MAX_EXPIRY_SECONDS). A run that stops
#     with terminal_reason "expired" ran out of TIME, and raising this number does nothing for it.
#   - Claude Code's own runtime, which may stop honouring a Stop hook after its own number of
#     consecutive blocks. This constant is the loop's budget, not the runtime's.
MAX_STOP_CONTINUATIONS = 10000
DEFAULT_MAX_ITERATIONS = MAX_STOP_CONTINUATIONS
MAX_ITERATIONS = MAX_STOP_CONTINUATIONS
GIT_TIMEOUT_SECONDS = 15
SESSION_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,255}\Z")


class StateError(RuntimeError):
    """Raised when loop state cannot be handled safely."""


class BusyStateError(StateError):
    """Raised when another process currently owns a state lock."""


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _canonical_path(path: str | os.PathLike[str]) -> Path:
    return Path(os.path.realpath(os.path.abspath(os.fspath(path))))


def _lexical_absolute_path(path: str | os.PathLike[str]) -> Path:
    return Path(os.path.abspath(os.path.expanduser(os.fspath(path))))


def validate_session_id(session_id: object) -> str:
    if not isinstance(session_id, str) or not SESSION_ID_PATTERN.fullmatch(session_id):
        raise StateError("invalid session_id")
    if len(session_id.encode("utf-8")) > MAX_SESSION_ID_BYTES:
        raise StateError("session_id is too large")
    return session_id


def _run_git(repo: Path, argument: str) -> str:
    # SECURITY-REVIEW: repository paths reach a subprocess only in the CLI/API;
    # argv is fixed, shell execution is disabled, and runtime is bounded.
    try:
        result = subprocess.run(
            ["git", "-C", os.fspath(repo), "rev-parse", argument],
            check=True,
            capture_output=True,
            text=True,
            timeout=GIT_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise StateError(f"unable to identify git repository: {exc}") from exc
    value = result.stdout.strip()
    if not value or "\x00" in value:
        raise StateError("git returned an invalid path")
    return value


def canonicalize_repository(
    repo: str | os.PathLike[str],
) -> tuple[Path, Path]:
    requested = _canonical_path(repo)
    if not requested.is_dir():
        raise StateError("repository path is not a directory")
    root = _canonical_path(_run_git(requested, "--show-toplevel"))
    common_value = _run_git(root, "--git-common-dir")
    common = _canonical_path(
        common_value if os.path.isabs(common_value) else root / common_value
    )
    if not root.is_dir() or not common.is_dir():
        raise StateError("git returned a missing repository directory")
    return root, common


def runtime_directory(*, create: bool) -> Path:
    configured = os.environ.get(RUNTIME_DIRECTORY_ENV, DEFAULT_RUNTIME_DIRECTORY)
    path = _lexical_absolute_path(configured)
    # SECURITY-REVIEW: this private, user-owned directory is the state
    # authenticity boundary. Its final path component must never be a symlink.
    try:
        metadata = os.lstat(path)
        existed = True
    except FileNotFoundError:
        existed = False
        if not create:
            return path
        try:
            os.mkdir(path, 0o700)
        except OSError as exc:
            raise StateError(f"unable to create runtime directory: {exc}") from exc
        metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise StateError("runtime path is not a safe directory")
    if metadata.st_uid != os.geteuid():
        raise StateError("runtime directory has the wrong owner")
    mode = stat.S_IMODE(metadata.st_mode)
    if create and mode != 0o700:
        os.chmod(path, 0o700, follow_symlinks=False)
        mode = stat.S_IMODE(os.lstat(path).st_mode)
    if mode != 0o700:
        raise StateError("runtime directory mode must be 0700")
    if not existed:
        _fsync_directory(path.parent)
    return path


def _repository_key(repo_root: Path) -> str:
    return hashlib.sha256(os.fspath(repo_root).encode("utf-8")).hexdigest()


def state_path_for(repo_root: Path) -> Path:
    return runtime_directory(create=False) / f"{_repository_key(_canonical_path(repo_root))}.json"


def lock_path_for(repo_root: Path) -> Path:
    return runtime_directory(create=False) / f"{_repository_key(_canonical_path(repo_root))}.lock"


def pointer_path() -> Path:
    """Where session→repository bindings live.

    The Stop payload carries a session's cwd and the loop is discovered from it. A session opened at
    a workspace PARENT — a directory that merely contains the repositories, which is ordinary — is
    inside no repository at all, so discovery finds nothing and the loop can never continue however
    much live state it has. These bindings are the explicit fallback.

    Isolated by the runtime-directory override so a test can never write the operator's real
    bindings, and the historical location otherwise, because sessions already armed reference it.
    Kept as ONE function because the same literal previously appeared in two runtime scripts, and a
    reader and a writer that disagree about the path is the same bug as having no writer at all.
    """
    configured = os.environ.get(RUNTIME_DIRECTORY_ENV)
    if configured:
        return _lexical_absolute_path(configured) / POINTER_FILENAME
    return _lexical_absolute_path("~/.claude") / POINTER_FILENAME


def _read_pointers() -> dict[str, Any]:
    """Current bindings, or an empty map. Never raises: a corrupt file must not break arming."""
    path = pointer_path()
    try:
        if not _assert_regular_path(path, allow_missing=True):
            return {}
        raw = _read_regular_file(path, MAX_STATE_BYTES)
        entries = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError, StateError):
        return {}
    return entries if isinstance(entries, dict) else {}


def _write_pointers(entries: dict[str, Any]) -> None:
    """Replace the bindings atomically. Never raises — a binding is a fallback, not the loop."""
    path = pointer_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        encoded = (
            json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False) + "\n"
        ).encode("utf-8")
        if len(encoded) > MAX_STATE_BYTES:
            return
        temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        descriptor = os.open(temporary, flags, 0o600)
        try:
            os.fchmod(descriptor, 0o600)
            _write_all(descriptor, encoded)
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
    except OSError:
        try:
            os.unlink(temporary)  # type: ignore[possibly-undefined]
        except (OSError, NameError):
            pass


def bind_session_repository(session_id: str, repo_root: Path) -> None:
    """Record that `session_id` drives the loop in `repo_root`.

    Called when the loop is ARMED, which is the only moment both facts are known together. Before
    this, the binding existed as a file two scripts read and nothing ever wrote — the workspace-parent
    fallback therefore fired only when some earlier session happened to have written it by hand.

    Bounded: the map is trimmed to the most recent entries so a long-lived home directory cannot grow
    it without limit. Never raises.
    """
    entries = _read_pointers()
    entries[session_id] = os.fspath(repo_root)
    if len(entries) > MAX_POINTER_ENTRIES:
        # Keep the newest by insertion order; dicts preserve it and rewriting an existing session
        # re-inserts it at the end, so the survivors are the sessions most recently armed.
        for stale in list(entries)[: len(entries) - MAX_POINTER_ENTRIES]:
            entries.pop(stale, None)
    _write_pointers(entries)


def unbind_session(session_id: str) -> None:
    """Drop a session's binding when its loop ends, so a dead loop is never resurrected by it."""
    entries = _read_pointers()
    if entries.pop(session_id, None) is not None:
        _write_pointers(entries)


def _assert_regular_path(
    path: Path,
    *,
    allow_missing: bool = False,
    required_mode: int | None = None,
) -> bool:
    try:
        metadata = os.lstat(path)
    except FileNotFoundError:
        if allow_missing:
            return False
        raise
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise StateError(f"unsafe non-regular file: {path}")
    if metadata.st_uid != os.geteuid():
        raise StateError(f"file has the wrong owner: {path}")
    if required_mode is not None and stat.S_IMODE(metadata.st_mode) != required_mode:
        raise StateError(f"file mode must be {required_mode:04o}: {path}")
    return True


@contextlib.contextmanager
def _locked(repo_root: Path) -> Iterator[None]:
    lock_path = lock_path_for(repo_root)
    existed = _assert_regular_path(
        lock_path, allow_missing=True, required_mode=0o600
    )
    flags = os.O_RDWR | os.O_CREAT | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise StateError("unsafe lock symlink") from exc
        raise StateError(f"unable to open state lock: {exc}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_uid != os.geteuid():
            raise StateError("unsafe state lock")
        if existed and stat.S_IMODE(metadata.st_mode) != 0o600:
            raise StateError("state lock mode must be 0600")
        if not existed:
            os.fchmod(descriptor, 0o600)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno in (errno.EACCES, errno.EAGAIN):
                raise BusyStateError("loop state is busy") from exc
            raise StateError(f"unable to lock loop state: {exc}") from exc
        yield
    finally:
        os.close(descriptor)


def _read_regular_file(
    path: Path,
    maximum_bytes: int,
    *,
    required_mode: int | None = None,
) -> bytes:
    # SECURITY-REVIEW: paths can originate from repositories or environment;
    # no-follow, nonblocking descriptors and fstat reject links/special files.
    flags = os.O_RDONLY | os.O_NONBLOCK
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        if exc.errno == errno.ELOOP:
            raise StateError(f"unsafe file symlink: {path}") from exc
        raise
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise StateError(f"unsafe non-regular file: {path}")
        if required_mode is not None:
            if metadata.st_uid != os.geteuid():
                raise StateError(f"file has the wrong owner: {path}")
            if stat.S_IMODE(metadata.st_mode) != required_mode:
                raise StateError(f"file mode must be {required_mode:04o}: {path}")
        if metadata.st_size > maximum_bytes:
            raise StateError(f"file exceeds {maximum_bytes} bytes")
        data = bytearray()
        while len(data) <= maximum_bytes:
            chunk = os.read(descriptor, min(65536, maximum_bytes + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > maximum_bytes:
            raise StateError(f"file exceeds {maximum_bytes} bytes")
        return bytes(data)
    finally:
        os.close(descriptor)


def _read_state(path: Path) -> dict[str, Any]:
    try:
        raw = _read_regular_file(path, MAX_STATE_BYTES, required_mode=0o600)
        state = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StateError(f"unable to read loop state: {exc}") from exc
    if not isinstance(state, dict):
        raise StateError("loop state is not a JSON object")
    return state


def _write_all(descriptor: int, data: bytes) -> None:
    offset = 0
    while offset < len(data):
        written = os.write(descriptor, data[offset:])
        if written <= 0:
            raise StateError("short write while saving loop state")
        offset += written


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _atomic_write_state(path: Path, state: dict[str, Any]) -> None:
    # SECURITY-REVIEW: global state is written through a same-directory
    # mode-0600 temporary file, fsynced, replaced, and parent-fsynced.
    encoded = (
        json.dumps(state, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_STATE_BYTES:
        raise StateError("serialized loop state is too large")
    _assert_regular_path(
        path, allow_missing=True, required_mode=0o600
    )
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = -1
    try:
        descriptor = os.open(temporary, flags, 0o600)
        os.fchmod(descriptor, 0o600)
        _write_all(descriptor, encoded)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = -1
        os.replace(temporary, path)
        _fsync_directory(path.parent)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _validate_state(state: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "active",
        "instance_id",
        "session_id",
        "canonical_repository_root",
        "git_common_directory",
        "created_at",
        "updated_at",
        "expires_at",
        "iteration",
        "max_iterations",
        "prompt",
        "terminal_reason",
    }
    if not required.issubset(state) or state["schema_version"] != SCHEMA_VERSION:
        raise StateError("invalid loop state schema")
    if not isinstance(state["active"], bool):
        raise StateError("invalid active field")
    for key in ("instance_id", "canonical_repository_root", "git_common_directory"):
        if not isinstance(state[key], str) or not state[key]:
            raise StateError(f"invalid {key} field")
    try:
        uuid.UUID(state["instance_id"])
    except (ValueError, AttributeError) as exc:
        raise StateError("invalid instance_id field") from exc
    validate_session_id(state["session_id"])
    for key in ("created_at", "updated_at", "expires_at"):
        value = state[key]
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
        ):
            raise StateError(f"invalid {key} field")
    for key in ("iteration", "max_iterations"):
        if not _is_int(state[key]):
            raise StateError(f"invalid {key} field")
    if not isinstance(state["prompt"], str):
        raise StateError("invalid prompt field")
    if len(state["prompt"].encode("utf-8")) > MAX_PROMPT_BYTES:
        raise StateError("prompt exceeds 64 KiB")
    terminal_reason = state["terminal_reason"]
    if terminal_reason is not None and not isinstance(terminal_reason, str):
        raise StateError("invalid terminal_reason field")
    if isinstance(terminal_reason, str):
        if len(terminal_reason.encode("utf-8")) > MAX_REASON_BYTES:
            raise StateError("terminal_reason exceeds 4 KiB")


def _terminate(state: dict[str, Any], reason: str, now: float) -> None:
    state["active"] = False
    state["prompt"] = ""
    state["terminal_reason"] = reason
    state["updated_at"] = now


def _normalize_state(
    state: dict[str, Any], now: float
) -> tuple[dict[str, Any], bool]:
    _validate_state(state)
    changed = False
    normalized_max = min(
        MAX_STOP_CONTINUATIONS, max(1, state["max_iterations"])
    )
    if normalized_max != state["max_iterations"]:
        state["max_iterations"] = normalized_max
        changed = True
    normalized_iteration = min(normalized_max, max(0, state["iteration"]))
    if normalized_iteration != state["iteration"]:
        state["iteration"] = normalized_iteration
        changed = True
    ceiling = state["created_at"] + MAX_EXPIRY_SECONDS
    if state["expires_at"] > ceiling:
        state["expires_at"] = ceiling
        changed = True
    if state["active"] and now >= state["expires_at"]:
        _terminate(state, "expired", now)
        changed = True
    elif not state["active"] and state["prompt"]:
        state["prompt"] = ""
        state["updated_at"] = now
        changed = True
    if changed:
        state["updated_at"] = now
    return state, changed


def _public_state(state: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in state.items() if key != "prompt"}


def _read_prompt(prompt_file: str | os.PathLike[str]) -> str:
    try:
        raw = _read_regular_file(_canonical_path(prompt_file), MAX_PROMPT_BYTES)
        return raw.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise StateError(f"unable to read prompt file: {exc}") from exc


def _require_identity(
    state: dict[str, Any],
    repo_root: Path,
    git_common_directory: Path,
) -> None:
    if state["canonical_repository_root"] != os.fspath(repo_root):
        raise StateError("state repository identity mismatch")
    if state["git_common_directory"] != os.fspath(git_common_directory):
        raise StateError("state git identity mismatch")


def _path_exists_without_following(path: Path) -> bool:
    try:
        os.lstat(path)
        return True
    except FileNotFoundError:
        return False


def start(
    repo: str | os.PathLike[str],
    prompt_file: str | os.PathLike[str],
    session_id: str,
    *,
    max_iter: int = DEFAULT_MAX_ITERATIONS,
    expires_in: int = 21600,
    now: float | None = None,
) -> dict[str, Any]:
    session_id = validate_session_id(session_id)
    root, common = canonicalize_repository(repo)
    runtime_directory(create=True)
    path = state_path_for(root)
    prompt = _read_prompt(prompt_file)
    current_time = time.time() if now is None else now
    with _locked(root):
        if _path_exists_without_following(path):
            existing, changed = _normalize_state(_read_state(path), current_time)
            _require_identity(existing, root, common)
            if changed:
                _atomic_write_state(path, existing)
            if existing["active"]:
                raise StateError("an active unexpired loop instance already exists")
        normalized_max = min(MAX_STOP_CONTINUATIONS, max(1, max_iter))
        normalized_expiry = min(MAX_EXPIRY_SECONDS, max(1, expires_in))
        state: dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            "active": True,
            "instance_id": str(uuid.uuid4()),
            "session_id": session_id,
            "canonical_repository_root": os.fspath(root),
            "git_common_directory": os.fspath(common),
            "created_at": current_time,
            "updated_at": current_time,
            "expires_at": current_time + normalized_expiry,
            "iteration": 0,
            "max_iterations": normalized_max,
            "prompt": prompt,
            "terminal_reason": None,
        }
        _atomic_write_state(path, state)
    # Outside the lock and deliberately non-fatal: the binding is a discovery FALLBACK, so failing
    # to record it must never fail an otherwise-armed loop.
    bind_session_repository(session_id, root)
    return _public_state(state)


def status(
    repo: str | os.PathLike[str], *, now: float | None = None
) -> dict[str, Any]:
    root, common = canonicalize_repository(repo)
    directory = runtime_directory(create=False)
    path = directory / f"{_repository_key(root)}.json"
    if not _path_exists_without_following(path):
        return {
            "schema_version": SCHEMA_VERSION,
            "active": False,
            "canonical_repository_root": os.fspath(root),
            "git_common_directory": os.fspath(common),
            "terminal_reason": "not_started",
        }
    current_time = time.time() if now is None else now
    with _locked(root):
        state, changed = _normalize_state(_read_state(path), current_time)
        _require_identity(state, root, common)
        if changed:
            _atomic_write_state(path, state)
    return _public_state(state)


def stop(
    repo: str | os.PathLike[str],
    instance_id: str,
    reason: str,
    session_id: str,
    *,
    now: float | None = None,
) -> dict[str, Any]:
    session_id = validate_session_id(session_id)
    if not reason or len(reason.encode("utf-8")) > MAX_REASON_BYTES:
        raise StateError("reason must be between 1 byte and 4 KiB")
    root, common = canonicalize_repository(repo)
    runtime_directory(create=False)
    path = state_path_for(root)
    current_time = time.time() if now is None else now
    with _locked(root):
        state, changed = _normalize_state(_read_state(path), current_time)
        _require_identity(state, root, common)
        if changed:
            _atomic_write_state(path, state)
            changed = False
        if state["instance_id"] != instance_id:
            raise StateError("instance_id does not match current loop instance")
        if state["session_id"] != session_id:
            raise StateError("session_id does not match current loop instance")
        if state["active"]:
            _terminate(state, reason, current_time)
            changed = True
        if changed:
            _atomic_write_state(path, state)
    # The loop is over, so drop the binding: a surviving entry would let a LATER turn of this same
    # session continue a loop that has already terminated.
    unbind_session(session_id)
    return _public_state(state)


def _safe_git_boundary(path: Path) -> tuple[Path, Path]:
    metadata = os.lstat(path)
    if stat.S_ISLNK(metadata.st_mode):
        raise StateError("unsafe .git symlink")
    if stat.S_ISDIR(metadata.st_mode):
        return path.parent, _canonical_path(path)
    if not stat.S_ISREG(metadata.st_mode):
        raise StateError("unsafe .git boundary")
    raw = _read_regular_file(path, MAX_GIT_FILE_BYTES)
    try:
        text = raw.decode("utf-8").strip()
    except UnicodeError as exc:
        raise StateError("invalid .git file") from exc
    if not text.startswith("gitdir: "):
        raise StateError("invalid .git file")
    git_value = text.removeprefix("gitdir: ").strip()
    if not git_value or "\x00" in git_value or "\n" in git_value:
        raise StateError("invalid .git directory")
    git_directory_path = _lexical_absolute_path(
        git_value if os.path.isabs(git_value) else path.parent / git_value
    )
    metadata = os.lstat(git_directory_path)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise StateError("unsafe git directory")
    git_directory = _canonical_path(git_directory_path)
    common_marker = git_directory / "commondir"
    if not _path_exists_without_following(common_marker):
        return path.parent, git_directory
    common_raw = _read_regular_file(common_marker, MAX_GIT_FILE_BYTES)
    try:
        common_value = common_raw.decode("utf-8").strip()
    except UnicodeError as exc:
        raise StateError("invalid commondir file") from exc
    if not common_value or "\x00" in common_value or "\n" in common_value:
        raise StateError("invalid common git directory")
    common_path = _lexical_absolute_path(
        common_value
        if os.path.isabs(common_value)
        else git_directory / common_value
    )
    metadata = os.lstat(common_path)
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise StateError("unsafe common git directory")
    common = _canonical_path(common_path)
    return path.parent, common


def ownership_status(repo_root, session_id, now=None) -> dict:
    """Why would tick() decline for this session? Read-only diagnosis; never mutates, never locks.

    tick() returns the same (False, None) whether NO loop is armed for a repository or a loop IS armed
    and belongs to somebody else, and the Stop hook allows both with suppressOutput. So losing your
    continuation looks exactly like never having had one: the loop stops advancing and reads as the
    assistant deciding to stop. That single ambiguity has now cost two separate agents a session each,
    and neither could tell it apart from an uninstalled hook.

    Returns a dict whose "state" is one of:
      "none"            no slot file for this repository
      "owned-by-other"  a slot is ACTIVE and owned by a DIFFERENT session   <- the silent killer
      "inactive"        slot exists but is finished or expired (terminal_reason says which)
      "capped"          this session owns it but has spent its continuations
      "ok"              this session owns an active slot with budget left
      "unknown"         unreadable or torn state, reported as unknown rather than guessed

    Lock-free on purpose: a diagnostic must never block a hook, never contend with a live tick, and
    never raise into a caller. Adding this does not change any decision — nothing here writes."""
    try:
        path = runtime_directory(create=False) / f"{_repository_key(_canonical_path(repo_root))}.json"
        if not _path_exists_without_following(path):
            return {"state": "none", "owner": None, "iteration": None,
                    "max_iterations": None, "terminal_reason": None}
        raw = json.loads(path.read_text("utf-8"))
        info = {
            "owner": raw.get("session_id"),
            "iteration": raw.get("iteration"),
            "max_iterations": raw.get("max_iterations"),
            "terminal_reason": raw.get("terminal_reason"),
        }
        current = time.time() if now is None else now
        if not raw.get("active") or current >= (raw.get("expires_at") or 0):
            return {"state": "inactive", **info}
        if info["owner"] != session_id:
            return {"state": "owned-by-other", **info}
        if (info["iteration"] or 0) >= (info["max_iterations"] or 0):
            return {"state": "capped", **info}
        return {"state": "ok", **info}
    except Exception:
        return {"state": "unknown", "owner": None, "iteration": None,
                "max_iterations": None, "terminal_reason": None}


def discover_repository(
    cwd: str | os.PathLike[str],
) -> tuple[Path, Path] | None:
    # SECURITY-REVIEW: hook cwd is untrusted. Canonical lexical ascent stops at
    # the nearest .git object and never executes git or walks past that boundary.
    current = _canonical_path(cwd)
    if not current.is_dir():
        return None
    while True:
        candidate = current / ".git"
        try:
            os.lstat(candidate)
        except FileNotFoundError:
            pass
        else:
            return _safe_git_boundary(candidate)
        parent = current.parent
        if parent == current:
            return None
        current = parent


def tick(
    repo_root: Path,
    git_common_directory: Path,
    session_id: str,
    *,
    now: float | None = None,
) -> tuple[bool, str | None]:
    session_id = validate_session_id(session_id)
    directory = runtime_directory(create=False)
    path = directory / f"{_repository_key(repo_root)}.json"
    if not _path_exists_without_following(path):
        return False, None
    current_time = time.time() if now is None else now
    with _locked(repo_root):
        state, changed = _normalize_state(_read_state(path), current_time)
        _require_identity(state, repo_root, git_common_directory)
        if not state["active"] or state["session_id"] != session_id:
            if changed:
                _atomic_write_state(path, state)
            return False, None
        if state["iteration"] >= state["max_iterations"]:
            _terminate(state, "continuation_cap", current_time)
            _atomic_write_state(path, state)
            return False, None
        state["iteration"] += 1
        state["updated_at"] = current_time
        prompt = state["prompt"]
        _atomic_write_state(path, state)
        return True, prompt


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    start_parser = commands.add_parser("start")
    start_parser.add_argument("--repo", required=True)
    start_parser.add_argument("--prompt-file", required=True)
    start_parser.add_argument("--session-id", required=True)
    start_parser.add_argument("--max-iter", type=int, default=DEFAULT_MAX_ITERATIONS)
    start_parser.add_argument("--expires-in", type=int, default=21600)
    status_parser = commands.add_parser("status")
    status_parser.add_argument("--repo", required=True)
    stop_parser = commands.add_parser("stop")
    stop_parser.add_argument("--repo", required=True)
    stop_parser.add_argument("--instance-id", required=True)
    stop_parser.add_argument("--session-id", required=True)
    stop_parser.add_argument("--reason", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "start":
            result = start(
                arguments.repo,
                arguments.prompt_file,
                arguments.session_id,
                max_iter=arguments.max_iter,
                expires_in=arguments.expires_in,
            )
        elif arguments.command == "status":
            result = status(arguments.repo)
        else:
            result = stop(
                arguments.repo,
                arguments.instance_id,
                arguments.reason,
                arguments.session_id,
            )
    except StateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
