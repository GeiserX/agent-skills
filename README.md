<p align="center">
  <img src="docs/images/banner.svg" alt="agent-skills" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/GeiserX/agent-skills?style=flat-square" alt="License"></a>
</p>

# agent-skills

Skills for [Claude Code](https://claude.com/claude-code) and [Codex](https://developers.openai.com/codex).
The durable loops drive a repository toward a goal. The parallel skills split a review, an
investigation, a research question or a change across independent agents. Each skill is one folder in
the shared `SKILL.md` format: `skills/` holds the Claude Code copies and `codex/skills/` the Codex ones.

## Features

- `/investigate`, `/review-pr`, `/review-code`, `/research` and `/implement` split the work across independent agents running in parallel, scaled to the size of the task, and check every finding before acting on it.
- `/sergio-loop` runs a durable goal loop in one repository: inspect and plan, implement, verify, then a fresh review, on the smallest unfinished slice.
- It keeps goals, evidence and human-only questions in `docs/`, and resumable state under `.omc/sergio-loop/`.
- An optional global Stop hook continues the loop in the same session and stays inert everywhere else.
- `/refine-loop` makes small, behavior-preserving improvements ranked by `ROI = Impact × Confidence ÷ Effort`, one per round, each checked by a fresh reviewer.
- `/docs-loop` audits documentation against the default branch, as a dry run, with staged edits, or with one pull request per repository. It never merges.
- None of them treats a stored goal as permission to merge, publish or deploy.
- `/kb-research` and `/kb-review` answer and review from your team's own record, through one adapter file you fill in for whatever knowledge base you have.
- A validator checks every skill package, and checks each loop against the shared loop contract.

## Quick start

```bash
git clone https://github.com/GeiserX/agent-skills.git && cd agent-skills
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/sergio-loop" ~/.claude/skills/sergio-loop
```

In Codex, link from `codex/skills/` into `~/.agents/skills/` instead and call a skill as `$<name>`. The loop Stop hook is Claude Code only.

Then run `/sergio-loop <goal>` in a fresh Claude Code session. If a skill of the same name is already installed, use the [installer](docs/installation.md), which moves it aside first. The same page installs the Stop hook.

## Documentation

- [Skills](docs/skills.md): what each skill does, its defaults and invocations, and how to use the goal loop and the parallel skills
- [Installation](docs/installation.md): the skill and hook installers, `settings.json` entries, canonical sources and local overlays
- [Development](docs/development.md): validating the skill packages and running the tests

## Other people's skills

`vendor/` holds skills written by other people, kept here as pinned snapshots with their licences. They are not installed by default; link the ones you want the same way as the others.

- [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT), 52 skills such as `unslop`, `blast-radius` and `show-me-your-work`, taken from Michael Denyer's [Claude Code port](https://github.com/michael-denyer/pstack-claude). Sources, commits and local changes are in [vendor/pstack/PROVENANCE.md](vendor/pstack/PROVENANCE.md).
- `writing-for-agents` from Matt Pocock's [skills](https://github.com/mattpocock/skills) (MIT). See [vendor/mattpocock-skills/PROVENANCE.md](vendor/mattpocock-skills/PROVENANCE.md).

## License

[GPL-3.0](LICENSE).
