# Related projects

## Skills from other projects

`vendor/` holds skills written by other people, kept as pinned snapshots with their MIT licences. The installer in [Getting started](getting-started.md) does not link them. Link the ones you want the same way, from the repository root:

```bash
ln -s "$PWD/vendor/pstack/skills/<name>" ~/.claude/skills/<name>
```

- **pstack**, from [cursor/plugins](https://github.com/cursor/plugins/tree/main/pstack) through its Claude Code port: 52 skills and 2 agents, such as `unslop`, `blast-radius` and `show-me-your-work`. The source commits, the local changes and the skills not to enable are in [vendor/pstack/PROVENANCE.md](https://github.com/GeiserX/agent-skills/blob/main/vendor/pstack/PROVENANCE.md).
- **writing-for-agents**, one skill copied unchanged from a public skills collection. The source, the commit and the licence are in [vendor/mattpocock-skills/PROVENANCE.md](https://github.com/GeiserX/agent-skills/blob/main/vendor/mattpocock-skills/PROVENANCE.md).

## Earlier repositories

- This repository was called `claude-skills`. GitHub redirects the old URLs here.
- [claude-code-parallel-skills](https://github.com/GeiserX/claude-code-parallel-skills) held the parallel skills before, as `/review-pr!` and the like, and needed oh-my-claudecode. It is archived; the skills now live here without the `!` and without that dependency.

## Where the skill formats are documented

- [Claude Code skills](https://code.claude.com/docs/en/skills)
- [Codex skills](https://developers.openai.com/codex/skills)
