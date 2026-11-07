# Getting started

Each skill is one folder in the shared `SKILL.md` format: `skills/` holds the Claude Code copies and `codex/skills/` the Codex ones. Pick one way to install for Claude Code: with both the plugin and the symlinks, every skill shows up twice.

## As a Claude Code plugin

```text
/plugin marketplace add GeiserX/sstack
/plugin install sstack@sstack
```

On Claude Code 2.1.275 or later, `/plugin install sstack --marketplace GeiserX/sstack` does both in one step. Plugin skills are namespaced: call them as `/sstack:full-loop`, `/sstack:file-pr` and so on. The plugin carries the skills only; the Stop hook below needs the installer.

## With npx

```bash
npx skills add GeiserX/sstack
```

## With the installer

```bash
git clone https://github.com/GeiserX/sstack && cd sstack && scripts/install.sh
```

`scripts/install.sh` links every skill from `skills/` into `~/.claude/skills/`. Name skills to link only
those (`scripts/install.sh file-pr revive`). Anything already at a destination is moved into
`~/.claude/skills-backups/<timestamp>-<pid>/` before the link is made, so a repeated install never nests a
link inside an old one. It refuses to run when `~/.claude/skills` is itself a link to this checkout.

For Codex, run `scripts/install.sh --codex`. It links `codex/skills/` into `~/.agents/skills/`, with backups
in `~/.agents/skills-backups/`. Codex calls a skill as `$<name>`, and the Codex copies run only when named
that way. The Stop hook below is Claude Code only, so in Codex each loop runs one pass per invocation,
saves its state and reports how to resume.

## The Stop hook

To let the goal loop continue in every repository, install the inert global runtime with `--hooks`
(add skill names or not, as above):

```bash
scripts/install.sh --hooks
```

It links `sergio_loop_state.py`, `sergio_loop_registration.py`, `sergio-loop-session-hook.py` and
`sergio-loop-stop-hook.py` from `runtime/` into `~/.claude/hooks/`, moving any existing files into
`~/.claude/hooks-backups/<timestamp>-<pid>/`, and prints the entries below. It never edits
`settings.json` itself.

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

If you run several Claude Code accounts, each with its own `CLAUDE_CONFIG_DIR` under one folder, the
SessionStart hook also adds the Stop entry to any account's `settings.json` that lacks it. It looks in
`~/.config/sstack/accounts/` by default; set `SERGIO_LOOP_ACCOUNTS_DIR` to point it at your folder. It only
ever adds a missing entry and never creates a settings file.

Restart Claude Code or open a fresh session after changing `settings.json`.

See the [Claude Code skills documentation](https://code.claude.com/docs/en/skills) for discovery and
invocation details.

## Canonical sources and local overlays

The public files in `skills/` are intentionally generic canonical sources. Local installed copies
may add private workspace policy as separate overlays. Keep those local additions out of
this repository instead of committing private policy into the canonical skills.

