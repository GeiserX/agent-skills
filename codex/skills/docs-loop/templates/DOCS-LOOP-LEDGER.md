# DOCS-LOOP LEDGER

> Frozen finite worklist and resume state. Append repository rows once, then update status and evidence in
> place. Process every row; do not extrapolate from clean repositories.

## Run

- state format: 1
- scope: {{SCOPE}}
- canonical scope fingerprint: {{SCOPE_FINGERPRINT}}
- mode: {{MODE}}
- state directory: {{STATE_DIR}}
- started: {{STARTED_AT}}
- repositories: {{REPO_COUNT}}
- result: IN-PROGRESS

## Repositories

| # | Canonical repository path | Remote | Default branch | Base commit | Branch | Worktree | Status | Deliverable / reason |
|---:|---|---|---|---|---|---|---|---|

<!-- Add exactly one row per frozen repository. Do not add example or placeholder repository rows. -->

## Status contract

- `PENDING`: frozen but not selected.
- `IN-PROGRESS`: selected and currently being processed.
- `DONE`: the authorized mode's deliverable completed with no unresolved candidate.
- `DEFERRED`: auditing completed, but one or more candidates require evidence or human intent.
- `SKIPPED`: duplicate, non-repository, instruction-excluded, or archived/read-only.
- `BLOCKED`: safety, authentication, permission, default-branch, scan, verification, push, PR, or CI failure.

Only `PENDING` may be selected. Resume `IN-PROGRESS` from its recorded worktree or mark it `BLOCKED` when
safe recovery is impossible. All other statuses are terminal.

## Result contract

- `SUCCESS`: all in-scope rows are `DONE` or benignly `SKIPPED`; none are deferred or blocked.
- `BLOCKED`: no row is `DONE` and at least one row is `BLOCKED`.
- `PARTIAL`: otherwise, any row or finding is `DEFERRED` or `BLOCKED`.

Any `BLOCKED` row prevents `SUCCESS`.
