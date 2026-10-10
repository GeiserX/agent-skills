<p align="center">
  <img src="docs/images/banner.svg" alt="agent-skills" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/GeiserX/agent-skills?style=flat-square" alt="License"></a>
</p>

# agent-skills

Skills for [Claude Code](https://claude.com/claude-code) and [Codex](https://developers.openai.com/codex).
The durable loops drive a repository toward a goal. The parallel skills split a review, an
investigation, a research question or a change across independent agents. The rest cover
shipping and growing a repository, replying, recovering cut-off work, and explaining.

## Features

- `/investigate`, `/review-pr`, `/review-code`, `/research` and `/implement` split the work across parallel agents, scaled to the size of the task, and check every finding before acting on it.
- `/sergio-loop` runs a durable goal loop in one repository, one small slice at a time, with goals and evidence in `docs/` and resumable state in `.omc/sergio-loop/`.
- An optional global Stop hook continues the loop in the same session and stays inert everywhere else.
- `/refine-loop` makes small, behavior-preserving improvements ranked by `ROI = Impact × Confidence ÷ Effort`, one per round, each checked by a fresh reviewer.
- `/docs-loop` audits documentation against the default branch, as a dry run, with staged edits, or with one pull request per repository. It never merges.
- None of them treats a stored goal as permission to merge, publish or deploy.
- `/kb-research` and `/kb-review` answer and review from your team's own record, through one adapter file you fill in for whatever knowledge base you have.
- `/grow-my-repo` plans where an open-source repository gets listed (GitHub itself, registries, directories, public catalogues, media, communities, funding) and does the submissions an agent may do. `/submit-awesome` sends one entry per awesome list, by each list's rules. Both hand the maintainer a packet wherever a place wants a human.
- `/file-pr` opens pull requests whose title says why the change matters and whose body starts with the problem. `/verified-reply` drafts a reply you send as yourself, every claim checked against a live source first.
- `/revive` brings work cut off by a usage limit, a crash or a compaction back from where it really stopped, and checks the world before every write so nothing happens twice.
- `/eli5` explains work or a system in plain words with real names, and `/help-decide` lays out a decision so one word answers it.
- A validator checks every skill package, and checks each loop against the shared loop contract.

## Quick start

```bash
git clone https://github.com/GeiserX/agent-skills.git && cd agent-skills
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/sergio-loop" ~/.claude/skills/sergio-loop
```

Then run `/sergio-loop <goal>` in a fresh Claude Code session. If a skill of the same name is already installed, the [installer](https://geiserx.github.io/agent-skills/getting-started/) moves it aside first and also installs the Stop hook. In Codex, link from `codex/skills/` into `~/.agents/skills/` and call a skill as `$<name>`; the Stop hook is Claude Code only.

## Documentation

The full documentation is at [geiserx.github.io/agent-skills](https://geiserx.github.io/agent-skills/).

- [Getting started](https://geiserx.github.io/agent-skills/getting-started/): the skill and hook installers, `settings.json` entries, canonical sources and local overlays
- [Usage](https://geiserx.github.io/agent-skills/usage/): what each skill does, its defaults and invocations, the goal loop, the parallel skills, the knowledge-base skills, and the skills for growing a repository, pull requests, replies and recovery
- [Development](https://geiserx.github.io/agent-skills/development/): validating the skill packages, rebuilding the Codex copies, running the tests
- [Related projects](https://geiserx.github.io/agent-skills/related/): the skills from other projects kept in `vendor/`, and the repository this one replaced

## Other people's skills

`vendor/` holds skills written by other people, kept here as pinned snapshots with their licences. They are not installed by default; link the ones you want the same way as the others.

- [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT), 52 skills such as `unslop`, `blast-radius` and `show-me-your-work`, taken from Michael Denyer's [Claude Code port](https://github.com/michael-denyer/pstack-claude). Sources, commits and local changes are in [vendor/pstack/PROVENANCE.md](vendor/pstack/PROVENANCE.md).
- `writing-for-agents` from Matt Pocock's [skills](https://github.com/mattpocock/skills) (MIT). See [vendor/mattpocock-skills/PROVENANCE.md](vendor/mattpocock-skills/PROVENANCE.md).

## License

[GPL-3.0-or-later](LICENSE)
