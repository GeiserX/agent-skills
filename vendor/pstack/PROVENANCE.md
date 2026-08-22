# Provenance

This directory vendors the pstack skill set for Claude Code. It is a snapshot, not a fork: to update, re-vendor from the sources below and re-apply the local deltas.

## Sources

| What | Source | Commit | License |
| --- | --- | --- | --- |
| 48 skills + `agents/poteto-agent.md` | [michael-denyer/pstack-claude](https://github.com/michael-denyer/pstack-claude) (Claude Code port of [cursor/plugins](https://github.com/cursor/plugins) `pstack/` + 7 `cursor-team-kit` skills) | `8bf501c1a9f6777f63f8d9a705c2b3f54a5b2eac` (2026-08-08, port v0.9.10, upstream v0.11.3) | MIT — see `LICENSE` (Lauren Tan), `LICENSE-cursor-team-kit` (Cursor), `NOTICE-port.md` |
| 4 skills the port does not carry yet: `bro`, `no-comments`, `swarm`, `technical-writing` + `agents/comment-sicko.md` | [cursor/plugins](https://github.com/cursor/plugins) `pstack/` | `46125561306434d8a1d7745d540d8932ab0cd2a2` (2026-08-20) | MIT — `LICENSE` |

The port was verified against real upstream at the attributed commits before vendoring: 7 skills byte-identical, the rest translation-only (Cursor primitives → Claude Code equivalents), zero injected content, and the four shipped scripts read line by line. `unslop/SKILL.md` is byte-identical to upstream.

## What is deliberately NOT here

- The port's plugin machinery: `commands/` trampolines, `hooks/` (the SessionStart mandate that auto-fires poteto-mode), `.claude-plugin/` manifests. We install skills bare; nothing here auto-fires at session start.

## Local deltas (re-apply after any re-vendor)

1. `bro`, `no-comments`, `swarm`, `technical-writing`: ported here directly from upstream. `bro` and `technical-writing` are verbatim. `swarm` and `no-comments` carry the port's standard substitutions (`Task`/`generalPurpose` → `Agent`/`general-purpose`, `~/.cursor/rules/pstack-models.mdc` → `~/.claude/pstack-models.md`, `grok-4.6-fast-xhigh` → `claude-sonnet-5`, `environment: "cloud"`/`cloud_base_branch` → `isolation: "remote"`/`"worktree"` platform notes).
2. `how` and `why` gained `disable-model-invocation: true`. Both fan out heavyweight explorer/investigator panels; the house rule is that questions are read-only and cheap, so they run only when invoked by name (`/how`, `/why`).

## House rules for this set

- Only skills symlinked into `~/.claude/skills/` load into sessions. The rest sit here as a library; enable one with `ln -s "$PWD/vendor/pstack/skills/<name>" ~/.claude/skills/<name>`.
- Never enable `setup-pstack`: it appends an include line to `~/.claude/CLAUDE.md`, and its model-override mechanism is pointless on this estate.
- Do not enable `deslop` or `tdd` under their upstream names: "deslop" and "tdd" are claimed trigger keywords of oh-my-claudecode (`ai-slop-cleaner`, TDD mode). Rename if ever needed.
- `babysit` and `poteto-mode/playbooks/autonomous-run.md` tell the agent to invoke a skill named `loop`. On this estate `loop` is the sergio-loop/refine-loop launcher — a real misfire path. Leave them unlinked, or edit that line first.
- Skill descriptions reference each other by sibling-relative paths (`../poteto-mode/references/...`). A dangling reference from an enabled skill to an unlinked one is a no-op note, not an error.
