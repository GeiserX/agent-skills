# claude-skills

Canonical, generic [Claude Code](https://claude.com/claude-code) skills for durable repository
workflows. Install a skill directory under `~/.claude/skills/` or a project's `.claude/skills/`;
the directory name becomes its slash command.

## Skills

### Goal loop: `/sergio-loop`

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

#### How to use the goal loop

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

### `/refine-loop`

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

### `/docs-loop`

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

## Canonical sources and local overlays

The public files in `skills/` are intentionally generic canonical sources. Local installed copies
may add private workspace or cmux policy as separate overlays. Keep those local additions out of
this repository instead of committing private policy into the canonical skills.

## Install

Run this from the repository root. Existing destinations are moved aside before each skill directory
is linked, preventing a repeated install from creating a nested self-symlink.

```bash
# SECURITY-REVIEW: Run only from this trusted checkout with the expected HOME.
install_root="$HOME/.claude/skills"
backup_root="$HOME/.claude/skills-backups/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$install_root" "$backup_root"

install_skill() {
  local skill="$1"
  local destination="$install_root/$skill"

  if [[ -e "$destination" || -L "$destination" ]]; then
    mv "$destination" "$backup_root/$skill"
  fi
  ln -s "$PWD/skills/$skill" "$destination"
}

install_skill sergio-loop
install_skill refine-loop
install_skill docs-loop
```

To let the goal loop continue in every repository, install the inert global runtime. The installer below
moves any existing hook files into the same timestamped backup directory used above:

```bash
# SECURITY-REVIEW: Install the reviewed runtime set together; do not mix versions.
hook_root="$HOME/.claude/hooks"
hook_backup_root="$HOME/.claude/hooks-backups/$(date +%Y%m%d-%H%M%S)-$$"
mkdir -p "$hook_root" "$hook_backup_root"

install_hook() {
  local file="$1"
  local destination="$hook_root/$file"

  if [[ -e "$destination" || -L "$destination" ]]; then
    mv "$destination" "$hook_backup_root/$file"
  fi
  ln -s "$PWD/runtime/$file" "$destination"
}

install_hook sergio_loop_state.py
install_hook sergio-loop-session-hook.py
install_hook sergio-loop-stop-hook.py
```

Merge these entries into `~/.claude/settings.json`; preserve any existing hooks such as notifications:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/sergio-loop-session-hook.py",
            "timeout": 10
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "python3 ~/.claude/hooks/sergio-loop-stop-hook.py",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
```

The SessionStart hook binds the loop to the exact Claude session. The Stop hook reads authenticated private
state outside the repository and blocks only for that active repository/session. Background tasks, scheduled
wakeups, unrelated sessions, inactive repositories, malformed state, and context/auth/rate-limit failures
are allowed to stop normally.

Restart Claude Code or open a fresh session after changing `settings.json`.

See the [Claude Code skills documentation](https://code.claude.com/docs/en/skills) for discovery and
invocation details.

## Validation

Validate all canonical skill packages:

```bash
python3 scripts/validate_skills.py skills \
  --contract shared/loop-contract.md
```

Run the validator tests:

```bash
python3 -m unittest discover -s tests
```

The suite includes the repository-agnostic global Stop runtime and cross-repository/session isolation tests.

## License

[GPL-3.0](LICENSE).
