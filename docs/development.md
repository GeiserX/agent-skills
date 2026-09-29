# Development

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

