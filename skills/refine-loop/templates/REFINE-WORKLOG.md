# REFINE WORKLOG — {{TARGET}}

Append-only evidence in `{{STATE_DIR}}`. Resume is valid only when `REFINE-GOAL.md`,
`REFINE-BACKLOG.md`, and `REFINE-WORKLOG.md` all exist with matching immutable state identity.

## State identity

- **format:** 1
- **target:** {{TARGET}}
- **state directory:** `{{STATE_DIR}}`
- **canonical repository root:** `{{CANONICAL_REPOSITORY_ROOT}}`
- **Git common directory:** `{{GIT_COMMON_DIR}}`

Current counters live only in `REFINE-BACKLOG.md`. Each round entry below records the counter
snapshot that resulted from that round.

## Preflight baseline

- **Branch or revision:** {{BASELINE_REVISION}}
- **Protected dirty paths:** {{PROTECTED_DIRTY_PATHS}}
- **Baseline checks:** {{BASELINE_CHECKS}}

## Rounds

<!-- For each completed round, append:
     - date, segment, round number, and covered lenses
     - discovered candidates and score evidence
     - NEEDS-FIX and goal handoffs
     - owned paths and exact change
     - focused and repository check results
     - fresh reviewer identity and verdict
     - rollback evidence when applicable
     - round, plateau_count, and fail_count after the round
     - terminal outcome or manual-resume status -->
