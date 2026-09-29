# Development

## Validation

Validate all canonical skill packages, then check that every loop packages the shared loop contract.
The parallel skills are not loops, so the contract check covers only the `*-loop` directories:

```bash
python3 scripts/validate_skills.py skills
python3 scripts/validate_skills.py skills/*-loop \
  --contract shared/loop-contract.md
```

`codex/skills/` is generated from `skills/`. Rebuild it after changing a skill, and commit both:

```bash
python3 scripts/build_codex.py
```

Each Codex copy is the canonical skill plus a "Running in Codex" section and an `agents/openai.yaml` that
turns off implicit invocation. The tests fail when `codex/skills/` is stale, so the validator runs on
`skills/` only.

Run the validator tests:

```bash
python3 -m unittest discover -s tests
```

The suite includes the repository-agnostic global Stop runtime and cross-repository/session isolation tests.

