from __future__ import annotations

import concurrent.futures
import fcntl
import importlib.util
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).parents[1]
RUNTIME = ROOT / "runtime"
STATE_SCRIPT = RUNTIME / "sergio_loop_state.py"
STOP_HOOK_SCRIPT = RUNTIME / "sergio-loop-stop-hook.py"
SESSION_HOOK_SCRIPT = RUNTIME / "sergio-loop-session-hook.py"
SPEC = importlib.util.spec_from_file_location("sergio_loop_state", STATE_SCRIPT)
assert SPEC and SPEC.loader
state_runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = state_runtime
SPEC.loader.exec_module(state_runtime)


class GlobalSergioLoopRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.global_runtime = self.root / "global-runtime"
        self.previous_runtime = os.environ.get(state_runtime.RUNTIME_DIRECTORY_ENV)
        os.environ[state_runtime.RUNTIME_DIRECTORY_ENV] = os.fspath(
            self.global_runtime
        )
        self.repo = self.make_repo("repo")
        self.prompt = self.root / "prompt.txt"
        self.prompt.write_text("Continue the verified task.", encoding="utf-8")

    def tearDown(self) -> None:
        if self.previous_runtime is None:
            os.environ.pop(state_runtime.RUNTIME_DIRECTORY_ENV, None)
        else:
            os.environ[state_runtime.RUNTIME_DIRECTORY_ENV] = self.previous_runtime
        self.temporary.cleanup()

    def make_repo(self, name: str) -> Path:
        repo = self.root / name
        repo.mkdir(parents=True)
        subprocess.run(
            ["git", "init", "-q", os.fspath(repo)],
            check=True,
            capture_output=True,
            timeout=20,
        )
        return repo.resolve()

    def state_path(self, repo: Path | None = None) -> Path:
        return state_runtime.state_path_for(repo or self.repo)

    def lock_path(self, repo: Path | None = None) -> Path:
        return state_runtime.lock_path_for(repo or self.repo)

    def read_state(self, repo: Path | None = None) -> dict[str, object]:
        return json.loads(self.state_path(repo).read_text(encoding="utf-8"))

    def start_loop(
        self,
        repo: Path | None = None,
        *,
        session_id: str = "session-a",
        max_iter: int = state_runtime.DEFAULT_MAX_ITERATIONS,
        expires_in: int = 21600,
        now: float | None = None,
    ) -> dict[str, object]:
        return state_runtime.start(
            repo or self.repo,
            self.prompt,
            session_id,
            max_iter=max_iter,
            expires_in=expires_in,
            now=now,
        )

    def run_stop_hook(
        self,
        repo: Path | None = None,
        *,
        cwd: Path | None = None,
        session_id: str | None = "session-a",
        camel_case_session: bool = False,
        extra: dict[str, object] | None = None,
        raw: bytes | None = None,
    ) -> tuple[subprocess.CompletedProcess[bytes], dict[str, object] | None]:
        payload: dict[str, object] = {"cwd": os.fspath(cwd or repo or self.repo)}
        if session_id is not None:
            payload["sessionId" if camel_case_session else "session_id"] = session_id
        if extra:
            payload.update(extra)
        result = subprocess.run(
            [sys.executable, os.fspath(STOP_HOOK_SCRIPT)],
            input=raw if raw is not None else json.dumps(payload).encode(),
            capture_output=True,
            timeout=10,
            env=os.environ.copy(),
        )
        output = json.loads(result.stdout) if result.stdout else None
        return result, output

    def assert_allow(self, result: subprocess.CompletedProcess[bytes]) -> None:
        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(
            b'{"continue":true,"suppressOutput":true}\n',
            result.stdout,
        )

    def test_repository_crafted_omc_state_is_ignored(self) -> None:
        local = self.repo / ".omc/sergio-loop/stop-state.json"
        local.parent.mkdir(parents=True)
        local.write_text(
            json.dumps(
                {
                    "active": True,
                    "session_id": "session-a",
                    "prompt": "repository-controlled prompt",
                }
            ),
            encoding="utf-8",
        )

        result, _ = self.run_stop_hook()

        self.assert_allow(result)
        self.assertFalse(self.global_runtime.exists())

    def test_session_start_appends_exact_export_without_output(self) -> None:
        env_file = self.root / "claude-env"
        env_file.write_text("EXISTING=value\n", encoding="utf-8")
        environment = os.environ.copy()
        environment["CLAUDE_ENV_FILE"] = os.fspath(env_file)

        result = subprocess.run(
            [sys.executable, os.fspath(SESSION_HOOK_SCRIPT)],
            input=json.dumps({"session_id": "session-a"}).encode(),
            capture_output=True,
            timeout=10,
            env=environment,
        )

        self.assertEqual(0, result.returncode)
        self.assertEqual(b"", result.stdout)
        self.assertEqual(b"", result.stderr)
        self.assertEqual(
            "EXISTING=value\nexport SERGIO_CLAUDE_SESSION_ID=session-a\n",
            env_file.read_text(encoding="utf-8"),
        )

    def test_session_start_rejects_symlink_and_invalid_session(self) -> None:
        target = self.root / "target-env"
        target.write_text("", encoding="utf-8")
        linked = self.root / "linked-env"
        os.symlink(target, linked)
        environment = os.environ.copy()
        environment["CLAUDE_ENV_FILE"] = os.fspath(linked)

        for env_file, session_id in (
            (linked, "session-a"),
            (target, "bad\nexport INJECTED=1"),
        ):
            environment["CLAUDE_ENV_FILE"] = os.fspath(env_file)
            result = subprocess.run(
                [sys.executable, os.fspath(SESSION_HOOK_SCRIPT)],
                input=json.dumps({"session_id": session_id}).encode(),
                capture_output=True,
                timeout=10,
                env=environment,
            )
            self.assertEqual(0, result.returncode)
            self.assertEqual(b"", result.stdout)

        self.assertEqual("", target.read_text(encoding="utf-8"))

    def test_start_and_stop_require_exact_session(self) -> None:
        with self.assertRaises(TypeError):
            state_runtime.start(self.repo, self.prompt)
        started = self.start_loop(session_id="owner")

        mismatch, _ = self.run_stop_hook(session_id="other")
        missing, _ = self.run_stop_hook(session_id=None)

        self.assert_allow(mismatch)
        self.assert_allow(missing)
        self.assertEqual(0, self.read_state()["iteration"])
        with self.assertRaises(state_runtime.StateError):
            state_runtime.stop(
                self.repo,
                started["instance_id"],
                "wrong session",
                "other",
            )

    def test_first_matching_stop_blocks_without_binding(self) -> None:
        self.start_loop(session_id="session-a")

        result, output = self.run_stop_hook(camel_case_session=True)

        self.assertEqual(0, result.returncode)
        self.assertEqual(
            {"decision": "block", "reason": "Continue the verified task."},
            output,
        )
        state = self.read_state()
        self.assertEqual("session-a", state["session_id"])
        self.assertEqual(1, state["iteration"])

    def test_active_replacement_rejected_and_expiry_clamped(self) -> None:
        first = self.start_loop(expires_in=state_runtime.MAX_EXPIRY_SECONDS * 2)
        self.assertEqual(
            state_runtime.MAX_EXPIRY_SECONDS,
            first["expires_at"] - first["created_at"],
        )

        with self.assertRaises(state_runtime.StateError):
            self.start_loop()

        self.assertEqual(first["instance_id"], self.read_state()["instance_id"])

    def test_nearest_nested_repository_never_uses_parent_state(self) -> None:
        self.start_loop()
        nested = self.make_repo("repo/nested")
        cwd = nested / "deeper"
        cwd.mkdir()

        result, _ = self.run_stop_hook(cwd=cwd)

        self.assert_allow(result)
        self.assertEqual(0, self.read_state()["iteration"])

    def test_subdirectory_discovers_nearest_repository(self) -> None:
        self.start_loop()
        subdirectory = self.repo / "nested/deeper"
        subdirectory.mkdir(parents=True)

        result, output = self.run_stop_hook(cwd=subdirectory)

        self.assertEqual("block", output["decision"])
        self.assertEqual(1, self.read_state()["iteration"])

    def test_stop_hook_does_not_invoke_git(self) -> None:
        self.start_loop()
        empty_path = self.root / "empty-path"
        empty_path.mkdir()
        previous_path = os.environ.get("PATH")
        os.environ["PATH"] = os.fspath(empty_path)
        try:
            result, output = self.run_stop_hook()
        finally:
            if previous_path is None:
                os.environ.pop("PATH", None)
            else:
                os.environ["PATH"] = previous_path

        self.assertEqual(0, result.returncode)
        self.assertEqual("block", output["decision"])

    def test_eight_blocks_then_ninth_allows_and_clears_prompt(self) -> None:
        started = self.start_loop(max_iter=500)
        self.assertEqual(8, started["max_iterations"])

        results = [self.run_stop_hook()[0] for _ in range(9)]

        for result in results[:8]:
            self.assertEqual("block", json.loads(result.stdout)["decision"])
        self.assert_allow(results[8])
        state = self.read_state()
        self.assertEqual(8, state["iteration"])
        self.assertFalse(state["active"])
        self.assertEqual("continuation_cap", state["terminal_reason"])
        self.assertEqual("", state["prompt"])

    def test_busy_lock_fails_open_in_hook_and_closed_in_cli(self) -> None:
        self.start_loop()
        descriptor = os.open(self.lock_path(), os.O_RDWR)
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
            hook_result, _ = self.run_stop_hook()
            cli_result = subprocess.run(
                [
                    sys.executable,
                    os.fspath(STATE_SCRIPT),
                    "status",
                    "--repo",
                    os.fspath(self.repo),
                ],
                capture_output=True,
                timeout=10,
                env=os.environ.copy(),
            )
        finally:
            os.close(descriptor)

        self.assert_allow(hook_result)
        self.assertEqual(2, cli_result.returncode)
        self.assertEqual(0, self.read_state()["iteration"])

    BLOCK = {"decision": "block", "reason": "Continue the verified task."}

    def test_listed_background_work_no_longer_latches_the_loop_off(self) -> None:
        """Merely LISTED work must not end the loop — only a human deciding to should.

        The gate this replaces allowed the stop whenever the payload carried any background task or
        cron. Both keep being reported after the work is over, and a task the runtime never reaps
        reports a running status forever, so one backgrounded command disabled continuation for the
        rest of the session — silently, and indistinguishably from an uninstalled hook. All three
        shapes below (bare entry, explicitly finished entry, cron map) must still continue.
        """
        self.start_loop()

        for extra in (
            {"background_tasks": ["task"]},
            {"background_tasks": [{"id": "t", "status": "completed"}]},
            {"session_crons": {"cron": "active"}},
        ):
            result, output = self.run_stop_hook(extra=extra)
            self.assertEqual(0, result.returncode, result.stderr.decode())
            self.assertEqual(self.BLOCK, output, f"listed work must not stop the loop: {extra}")

        self.assertEqual(3, self.read_state()["iteration"])

    def test_start_binds_the_session_to_its_repository_and_stop_clears_it(self) -> None:
        """The binding must be WRITTEN by arming.

        It was read by two runtime scripts and written by nothing, so the workspace-parent fallback
        below fired only when some earlier session happened to have written the file by hand.
        """
        started = self.start_loop()
        pointers = json.loads(state_runtime.pointer_path().read_text(encoding="utf-8"))
        self.assertEqual(os.fspath(self.repo), pointers.get("session-a"))

        state_runtime.stop(self.repo, started["instance_id"], "success", "session-a")

        pointers = json.loads(state_runtime.pointer_path().read_text(encoding="utf-8"))
        self.assertNotIn(
            "session-a", pointers, "a terminated loop must not stay resurrectable by its binding"
        )

    def test_a_workspace_parent_cwd_continues_through_the_binding(self) -> None:
        """A cwd that merely CONTAINS the repositories is inside none of them.

        Discovery therefore finds nothing and the loop could never continue, however much live state
        it had — the exact silent stop this fallback exists for.
        """
        self.start_loop()
        self.assertIsNone(
            state_runtime.discover_repository(os.fspath(self.root)),
            "precondition: the workspace parent must not itself be a repository",
        )

        result, output = self.run_stop_hook(cwd=self.root)

        self.assertEqual(0, result.returncode, result.stderr.decode())
        self.assertEqual(self.BLOCK, output)
        self.assertEqual(1, self.read_state()["iteration"])

    def test_a_cwd_in_an_unlooped_repository_still_continues_its_bound_loop(self) -> None:
        """Discovery SUCCEEDING is not enough: it can resolve to a repository that has no loop.

        A shared workspace — several repositories under one parent, one loop slot per repository —
        would otherwise stop silently, because the binding was consulted only when discovery failed.
        """
        other = self.make_repo("other")
        self.start_loop()

        result, output = self.run_stop_hook(cwd=other)

        self.assertEqual(self.BLOCK, output)
        self.assertEqual(1, self.read_state()["iteration"])

    def test_a_binding_never_reaches_down_into_a_nested_repository(self) -> None:
        """The binding must not resurrect the parent-state hijack the nearest-repository rule forbids.

        Arming binds the session to the OUTER repository, which is ordinary. A later turn whose cwd is
        inside a repository nested within it must still be governed by that nested repository — the
        fallback is for repositories discovery cannot reach, never a way back to an enclosing one.
        (The sibling case above proves the fallback still works where it should.)
        """
        self.start_loop()
        nested = self.make_repo("repo/nested")
        deeper = nested / "deeper"
        deeper.mkdir()

        result, _ = self.run_stop_hook(cwd=deeper)

        self.assert_allow(result)
        self.assertEqual(0, self.read_state()["iteration"])

    def test_a_binding_never_continues_another_sessions_loop(self) -> None:
        """The fallback must not become a way for any session to drive a loop it does not own."""
        self.start_loop(session_id="session-a")

        result, _ = self.run_stop_hook(cwd=self.root, session_id="session-b")

        self.assert_allow(result)
        self.assertEqual(0, self.read_state()["iteration"])

    def test_bindings_are_bounded(self) -> None:
        """A home directory lives for years; the map must not grow without limit."""
        for index in range(state_runtime.MAX_POINTER_ENTRIES + 5):
            state_runtime.bind_session_repository(f"session-{index}", self.repo)

        pointers = json.loads(state_runtime.pointer_path().read_text(encoding="utf-8"))
        self.assertEqual(state_runtime.MAX_POINTER_ENTRIES, len(pointers))
        self.assertNotIn("session-0", pointers, "the oldest binding must be evicted first")
        self.assertIn(
            f"session-{state_runtime.MAX_POINTER_ENTRIES + 4}",
            pointers,
            "the most recently armed session must survive",
        )

    def test_stop_and_expiry_clear_prompt_atomically(self) -> None:
        started = self.start_loop(session_id="owner")
        stopped = state_runtime.stop(
            self.repo,
            started["instance_id"],
            "operator requested",
            "owner",
        )
        self.assertFalse(stopped["active"])
        self.assertNotIn("prompt", stopped)
        self.assertEqual("", self.read_state()["prompt"])

        replacement = self.start_loop(session_id="owner", now=1000.0, expires_in=1)
        with self.assertRaises(state_runtime.StateError):
            state_runtime.stop(
                self.repo,
                replacement["instance_id"],
                "wrong session",
                "intruder",
                now=1001.0,
            )
        expired = state_runtime.status(self.repo, now=1001.0)
        self.assertNotEqual(started["instance_id"], replacement["instance_id"])
        self.assertFalse(expired["active"])
        self.assertEqual("expired", expired["terminal_reason"])
        self.assertEqual("", self.read_state()["prompt"])

    def test_global_directory_state_and_lock_modes(self) -> None:
        self.start_loop()

        self.assertEqual(
            0o700, stat.S_IMODE(self.global_runtime.stat().st_mode)
        )
        self.assertEqual(0o600, stat.S_IMODE(self.state_path().stat().st_mode))
        self.assertEqual(0o600, stat.S_IMODE(self.lock_path().stat().st_mode))
        self.assertEqual(
            [],
            list(self.global_runtime.glob(f".{self.state_path().name}.*.tmp")),
        )
        self.assertFalse(
            (self.repo / ".omc/sergio-loop/stop-state.json").exists()
        )

    def test_two_repositories_have_separate_hashed_state(self) -> None:
        other = self.make_repo("other")
        first = self.start_loop(self.repo, session_id="first")
        second = self.start_loop(other, session_id="second")

        blocked, _ = self.run_stop_hook(self.repo, session_id="first")

        self.assertEqual("block", json.loads(blocked.stdout)["decision"])
        self.assertNotEqual(first["instance_id"], second["instance_id"])
        self.assertNotEqual(self.state_path(self.repo), self.state_path(other))
        self.assertEqual(0, self.read_state(other)["iteration"])

    def test_symlink_global_directory_and_state_fail_safely(self) -> None:
        target_directory = self.root / "runtime-target"
        target_directory.mkdir(mode=0o700)
        os.symlink(target_directory, self.global_runtime)

        with self.assertRaises(state_runtime.StateError):
            self.start_loop()
        global_link_hook, _ = self.run_stop_hook()
        self.assert_allow(global_link_hook)

        self.global_runtime.unlink()
        self.start_loop()
        outside = self.root / "outside-state"
        outside.write_text("{}", encoding="utf-8")
        self.state_path().unlink()
        os.symlink(outside, self.state_path())

        state_link_hook, _ = self.run_stop_hook()
        self.assert_allow(state_link_hook)
        with self.assertRaises(state_runtime.StateError):
            state_runtime.status(self.repo)

    def test_malformed_and_mismatched_global_state_fail_open(self) -> None:
        self.start_loop()
        self.state_path().write_text("{bad json", encoding="utf-8")
        malformed, _ = self.run_stop_hook()
        self.assert_allow(malformed)

        self.state_path().unlink()
        replacement = self.start_loop()
        state = self.read_state()
        state["canonical_repository_root"] = os.fspath(self.root)
        self.state_path().write_text(json.dumps(state), encoding="utf-8")
        os.chmod(self.state_path(), 0o600)

        mismatched, _ = self.run_stop_hook()
        self.assert_allow(mismatched)
        self.assertEqual(replacement["instance_id"], self.read_state()["instance_id"])

    def test_context_auth_and_rate_limit_reasons_allow_without_tick(self) -> None:
        self.start_loop()
        reasons = (
            "context window exceeded",
            "token limit reached",
            "authentication failed",
            "auth_error",
            "HTTP 401",
            "HTTP 403",
            "OAuth refresh failed",
            "rate-limit exceeded",
            "HTTP 429 too many requests",
        )

        for reason in reasons:
            with self.subTest(reason=reason):
                result, _ = self.run_stop_hook(extra={"reason": reason})
                self.assert_allow(result)

        self.assertEqual(0, self.read_state()["iteration"])

    def test_assistant_text_does_not_masquerade_as_stop_reason(self) -> None:
        self.start_loop()

        result, output = self.run_stop_hook(
            extra={"last_assistant_message": "The rate limit policy is documented."}
        )

        self.assertEqual("block", output["decision"])
        self.assertEqual(1, self.read_state()["iteration"])

    def test_stale_instance_cannot_stop_replacement(self) -> None:
        first = self.start_loop(session_id="owner")
        state_runtime.stop(
            self.repo, first["instance_id"], "first complete", "owner"
        )
        second = self.start_loop(session_id="owner")

        with self.assertRaises(state_runtime.StateError):
            state_runtime.stop(
                self.repo, first["instance_id"], "stale cleanup", "owner"
            )

        current = state_runtime.status(self.repo)
        self.assertTrue(current["active"])
        self.assertEqual(second["instance_id"], current["instance_id"])

    def test_status_and_cli_output_never_expose_prompt(self) -> None:
        secret_prompt = self.root / "secret-prompt.txt"
        secret_prompt.write_text("PRIVATE LOOP PROMPT", encoding="utf-8")
        state_runtime.start(self.repo, secret_prompt, "owner")

        status = state_runtime.status(self.repo)
        cli = subprocess.run(
            [
                sys.executable,
                os.fspath(STATE_SCRIPT),
                "status",
                "--repo",
                os.fspath(self.repo),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=os.environ.copy(),
        )

        self.assertNotIn("prompt", status)
        self.assertNotIn("PRIVATE LOOP PROMPT", cli.stdout)
        self.assertNotIn("prompt", json.loads(cli.stdout))

    def test_cli_lifecycle_requires_session_id(self) -> None:
        missing_session = subprocess.run(
            [
                sys.executable,
                os.fspath(STATE_SCRIPT),
                "start",
                "--repo",
                os.fspath(self.repo),
                "--prompt-file",
                os.fspath(self.prompt),
            ],
            capture_output=True,
            timeout=10,
            env=os.environ.copy(),
        )
        self.assertEqual(2, missing_session.returncode)

        start = subprocess.run(
            [
                sys.executable,
                os.fspath(STATE_SCRIPT),
                "start",
                "--repo",
                os.fspath(self.repo),
                "--prompt-file",
                os.fspath(self.prompt),
                "--session-id",
                "owner",
                "--max-iter",
                "99",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=os.environ.copy(),
        )
        started = json.loads(start.stdout)
        self.assertEqual(8, started["max_iterations"])

        stopped = subprocess.run(
            [
                sys.executable,
                os.fspath(STATE_SCRIPT),
                "stop",
                "--repo",
                os.fspath(self.repo),
                "--instance-id",
                started["instance_id"],
                "--session-id",
                "owner",
                "--reason",
                "operator requested",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
            env=os.environ.copy(),
        )
        stopped_state = json.loads(stopped.stdout)
        self.assertFalse(stopped_state["active"])
        self.assertEqual("", self.read_state()["prompt"])

    def test_concurrent_hooks_never_over_tick(self) -> None:
        self.start_loop()

        def invoke(_: int) -> subprocess.CompletedProcess[bytes]:
            return self.run_stop_hook()[0]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
            results = list(executor.map(invoke, range(8)))

        outputs = [json.loads(result.stdout) for result in results]
        blocked = sum(output.get("decision") == "block" for output in outputs)
        self.assertTrue(
            all(
                output.get("decision") == "block"
                or output == {"continue": True, "suppressOutput": True}
                for output in outputs
            )
        )
        self.assertEqual(blocked, self.read_state()["iteration"])
        for _ in range(8 - blocked):
            result, output = self.run_stop_hook()
            self.assertEqual("block", output["decision"], result.stderr.decode())
        self.assertEqual(8, self.read_state()["iteration"])
        ninth, _ = self.run_stop_hook()
        self.assert_allow(ninth)

    def test_prompt_size_is_bounded(self) -> None:
        oversized = self.root / "oversized.txt"
        oversized.write_bytes(b"x" * (state_runtime.MAX_PROMPT_BYTES + 1))

        with self.assertRaises(state_runtime.StateError):
            state_runtime.start(self.repo, oversized, "owner")


if __name__ == "__main__":
    unittest.main()
