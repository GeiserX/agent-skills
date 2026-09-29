<p align="center">
  <img src="docs/images/banner.svg" alt="claude-skills" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/github/license/GeiserX/claude-skills?style=flat-square" alt="License"></a>
</p>

# claude-skills

Canonical, generic [Claude Code](https://claude.com/claude-code) skills for durable repository
workflows. Install a skill directory under `~/.claude/skills/` or a project's `.claude/skills/`;
the directory name becomes its slash command.

## Features

- `/sergio-loop` runs a durable goal loop in one repository: inspect and plan, implement, verify, then a fresh review, on the smallest unfinished slice.
- It keeps goals, evidence and human-only questions in `docs/`, and resumable state under `.omc/sergio-loop/`.
- An optional global Stop hook continues the loop in the same session and stays inert everywhere else.
- `/refine-loop` makes small, behavior-preserving improvements ranked by `ROI = Impact × Confidence ÷ Effort`, one per round, each checked by a fresh reviewer.
- `/docs-loop` audits documentation against the default branch, as a dry run, with staged edits, or with one pull request per repository. It never merges.
- None of them treats a stored goal as permission to merge, publish or deploy.
- A validator checks every skill package against the shared loop contract.

## Quick start

```bash
git clone https://github.com/GeiserX/claude-skills.git && cd claude-skills
mkdir -p ~/.claude/skills && ln -s "$PWD/skills/sergio-loop" ~/.claude/skills/sergio-loop
```

Then run `/sergio-loop <goal>` in a fresh Claude Code session. If a skill of the same name is already installed, use the [installer](docs/installation.md), which moves it aside first. The same page installs the Stop hook.

## Documentation

- [Skills](docs/skills.md): what each skill does, its defaults and invocations, and how to use the goal loop
- [Installation](docs/installation.md): the skill and hook installers, `settings.json` entries, canonical sources and local overlays
- [Development](docs/development.md): validating the skill packages and running the tests

## License

[GPL-3.0](LICENSE).
