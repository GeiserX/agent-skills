# REFINE BACKLOG — {{TARGET}}

This file is the authoritative stop state in `{{STATE_DIR}}`. Resume is valid only when
`REFINE-GOAL.md`, `REFINE-BACKLOG.md`, and `REFINE-WORKLOG.md` all exist and agree.

## State identity

- **format:** 1
- **target:** {{TARGET}}
- **state directory:** `{{STATE_DIR}}`
- **canonical repository root:** `{{CANONICAL_REPOSITORY_ROOT}}`
- **Git common directory:** `{{GIT_COMMON_DIR}}`

## Loop state

- **outcome:** none
- **segment:** 1
- **round:** 0 / 25
- **theta:** 2.0
- **plateau_count:** 0 / 3
- **fail_count:** 0 / 3
- **last_completed_round:** none

Outcome is one of `SUCCESS`, `BUDGET`, `ERROR`, `NEEDS-FIX`, or `CANCELLED` only when terminal.

## Candidates

| ID | Lens | Finding family | Evidence | Impact | Confidence | Effort | ROI | Status |
|---|---|---|---|---:|---:|---:|---:|---|

Candidate status: `proposed`, `accepted`, `below-threshold`, `cooldown`, `blocked-protected-path`, or
`rolled-back`.

## NEEDS-FIX handoffs

| ID | Severity | Class | Evidence | Recommended workflow | Status |
|---|---|---|---|---|---|

Use this section for correctness, security, privacy, data-loss, destructive-operation, or other
behavior-changing findings. This loop does not execute them. Status is `open` or `handed-off`.

## Out-of-scope goal handoffs

| ID | Lens | Desired behavior change | Evidence | Status |
|---|---|---|---|---|

## Protected baseline paths

No paths recorded.

## Finding-family cooldowns

No families on cooldown.
