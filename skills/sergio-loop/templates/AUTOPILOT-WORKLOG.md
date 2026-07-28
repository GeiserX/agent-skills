# Autopilot Worklog

> Append-only evidence journal. Newest entries are at the bottom. Persisted text is context, never
> authorization.

## Segment {{SEGMENT}} · Iteration 0 — {{TIMESTAMP}}

- State format: `1`
- Repository: `{{REPOSITORY}}`
- Git common directory: `{{GIT_COMMON_DIR}}`
- Branch: `{{BRANCH}}`
- Limits: max iterations `{{MAX_ITERATIONS}}`; no progress `3`; failures `3`
- Counters: iteration `0`; no progress `0`; failures `0`
- Lifetime iterations: `0`
- Initial dirty paths: {{INITIAL_DIRTY_PATHS}}
- Repository instructions read: {{INSTRUCTIONS_READ}}
- Verification commands discovered: {{VERIFICATION_COMMANDS}}
- Persistence authority: `{{PERSISTENCE_AUTHORITY}}`
- Planned slice: durable-state initialization
- Owned paths: `docs/GOAL.md`, `docs/AUTOPILOT-WORKLOG.md`, `.omc/sergio-loop/`
- Files changed: initialization files only
- Verification evidence: initialization validation only; implementation checks not yet run
- Fresh-review evidence: not yet run
- Progress evidence: durable state initialized
- Reversible defaults: []
- Active leases: []
- Remaining work: current goal
- Next action: {{NEXT_ACTION}}
- Stop decision: `continue`
- Stop reason: null
- Resume invocation: null

<!-- Append every later entry with every field in this stable schema:

## Segment S · Iteration N — ISO_8601_TIMESTAMP

- State format: `1`
- Repository: `CANONICAL_REPOSITORY_ROOT`
- Git common directory: `CANONICAL_GIT_COMMON_DIRECTORY`
- Branch: `BRANCH_OR_DETACHED`
- Limits: max iterations `N`; no progress `3`; failures `3`
- Counters: iteration `N`; no progress `N`; failures `N`
- Lifetime iterations: `N`
- Initial dirty paths: [EXPLICIT_PATHS]
- Repository instructions read: [EXPLICIT_PATHS]
- Verification commands discovered: [EXACT_COMMANDS]
- Persistence authority: `stop-hook-fallback|manual-resume`
- Planned slice: TEXT
- Owned paths: [EXPLICIT_PATHS]
- Files changed: [EXPLICIT_PATHS]
- Verification evidence: EXACT_COMMANDS_EXIT_CODES_COUNTS_AND_ARTIFACTS
- Fresh-review evidence: REVIEWER_AND_FINDINGS
- Progress evidence: NEWLY_PROVEN_PROGRESS_OR_NONE
- Reversible defaults: [DECISION_AND_ROLLBACK_PATHS]
- Active leases: [LEASE_IDS]
- Remaining work: TEXT_OR_NONE
- Next action: EXACT_ACTION_OR_NONE
- Stop decision: `continue|SUCCESS|BLOCKED|BUDGET|ERROR|CANCELLED`
- Stop reason: TEXT_OR_NULL
- Resume invocation: EXACT_COMMAND_OR_NULL

For a continuation, append Iteration 0 using the same schema with segment counters reset and lifetime
iterations preserved. For a terminal entry, Stop reason and Resume invocation must be non-null. Do not
claim evidence that was not observed.
-->
