# Skills

## Goal loop: `/sergio-loop`

A durable, direct goal loop for one repository. It inspects and plans, implements, verifies, and
fresh-reviews the smallest unfinished slice without invoking nested slash commands.

- Appends exact goals and continuation history to `docs/GOAL.md`, evidence to
  `docs/AUTOPILOT-WORKLOG.md`, and genuine human-only decisions to
  `docs/DEFERRED-QUESTIONS.md`.
- Keeps resumable machine state, provenance, locking, and optional leases under
  `.omc/sergio-loop/`.
- Defaults to `max_iterations=50`, `no_progress_limit=3`, and `failure_limit=3`. Only
  `max_iterations` is configurable.
- `--coordinate` adds the append-only `docs/COORDINATE.md` board and lease-backed mutual exclusion.
  The ordinary word `coordinate` inside a goal does not enable this mode.
- `--continue` is required to reopen a terminal run. A completed `SUCCESS` run also requires a new
  goal; other terminal runs may resume the latest goal or append a new one.
- A compatible persistence-only Stop-hook may continue the loop. OMC Ralph is a separate full
  execution workflow and must be invoked separately, never stacked as a continuation adapter.
  Without a compatible hook, the skill completes one iteration, saves state, and reports the manual
  resume invocation.
- Persisted goals and prior approvals are context, not authorization. Merge, publish, deploy,
  production mutation, destructive history changes, and other external side effects require
  authorization in the current invocation or confirmation in the current session.

```text
/sergio-loop <goal>
/sergio-loop --coordinate --max-iterations=20 <goal>
/sergio-loop
/sergio-loop --continue
/sergio-loop --continue <new goal>
```

### How to use the goal loop

1. Start a fresh Claude Code session in the target Git repository. A fresh session is required after first
   installing the hooks so `SessionStart` can export the exact Claude session identity.
2. Run `/sergio-loop <goal>`. The goal is stored verbatim, then the loop performs direct
   inspect/plan → implement → verify → fresh-review iterations.
3. The global Stop hook continues the same loop for up to eight consecutive Stop events. This is Claude
   Code's platform cap, not a configurable skill limit.
4. If the platform cap ends a still-active segment, run `/sergio-loop` with no new goal to resume that
   nonterminal state. Use `--continue` only to reopen a terminal `SUCCESS`, `BLOCKED`, `BUDGET`, `ERROR`, or
   `CANCELLED` run.
5. The Stop hook is inert in repositories without an active goal loop and ignores other Claude sessions in
   the same repository.

## `/refine-loop`

A resumable loop for small improvements that preserve the observable behavior of an already working
repository. It is not a feature, bug-fix, security-remediation, migration, or rewrite workflow.

- Audits architecture, usability, production readiness, and refactoring, then ranks eligible
  candidates with `ROI = Impact × Confidence ÷ Effort`.
- Defaults to `theta=2.0`, `plateau_limit=3`, `max_rounds=25`, `failure_limit=3`,
  `state_dir=.refine-loop/`, all four lenses, and the current repository.
- Accepts at most one candidate per round. Every accepted change must pass repository checks and a
  fresh read-only reviewer; the implementer cannot self-approve.
- Records correctness, security, privacy, data-loss, destructive-operation, product, and other
  behavior-changing findings as `NEEDS-FIX` handoffs to a dedicated fix or goal workflow. A critical
  finding ends the round with `NEEDS-FIX`.
- A host persistence-only interface may continue the exact same workflow. OMC Ralph does not qualify;
  without a compatible interface, the loop saves state after the current pass and reports how to resume.

```text
/refine-loop <intent>
/refine-loop theta=1.5 focus=usability,refactoring <intent>
/refine-loop --continue
```

## `/docs-loop`

A finite, default-branch documentation audit across one repository, explicit repository paths, or
repositories discovered below an explicit root.

- **DRY-RUN** (no leading `--apply`) reads and reports only. It does not edit tracked files or write
  state.
- **APPLY** (`--apply`) may update state and make supported documentation-only edits serially in
  isolated worktrees. It leaves exact changed documentation paths staged but does not commit, push,
  or open pull requests.
- **OPEN-PRS** (`--apply --open-prs`) additionally authorizes commits, branch pushes, and one pull
  request per repository, including required-check verification.
- Every mode preserves unsupported or uncertain claims as deferrals. No mode authorizes merging,
  releasing, or deploying. `/docs-loop` never merges.

```text
/docs-loop
/docs-loop REPO_PATH ...
/docs-loop --root=PATH
/docs-loop --apply REPO_PATH ...
/docs-loop --apply --open-prs --root=PATH
```

