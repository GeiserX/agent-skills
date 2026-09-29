# Development

## Validation

Validate all canonical skill packages, then check that every loop packages the shared loop contract.
The parallel skills are not loops, so the contract check covers only the `*-loop` directories:

```bash
python3 scripts/validate_skills.py skills
python3 scripts/validate_skills.py skills/*-loop \
  --contract shared/loop-contract.md
```

Run the validator tests:

```bash
python3 -m unittest discover -s tests
```

The suite includes the repository-agnostic global Stop runtime and cross-repository/session isolation tests.

