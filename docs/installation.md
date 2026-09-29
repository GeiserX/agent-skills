# Installation

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

## Canonical sources and local overlays

The public files in `skills/` are intentionally generic canonical sources. Local installed copies
may add private workspace or cmux policy as separate overlays. Keep those local additions out of
this repository instead of committing private policy into the canonical skills.

