# refine-loop four-lens evidence prompts

Use these prompts to discover candidates, not as universal standards. Repository policy, product
requirements, measured behavior, user evidence, and applicable regulations take precedence.

Every finding needs concrete evidence. A number, style preference, named pattern, or industry
framework is not sufficient by itself. Explain the present cost or risk in this repository.

This loop executes only behavior-preserving refinements. Correctness, security, privacy, data-loss,
destructive-operation, and desired product-behavior findings are recorded as `NEEDS-FIX` handoffs
for a dedicated fix or goal workflow. They are never silently ignored and never implemented by the
refinement loop.

## Lens 1: Architecture and code health

### Boundaries and dependencies

- Look for modules that change together often, reach into each other's internals, or share mutable
  global state. Use import graphs, change history, and call sites as evidence.
- Check whether dependency direction matches the repository's intended boundaries. A forbidden
  import or dependency cycle matters when it creates coupled releases, difficult tests, or unsafe
  changes.
- Prefer capability-oriented organization only when it clarifies ownership or reduces change
  spread. Directory naming alone is not evidence.

### Cohesion and duplication

- Find files or functions that combine unrelated reasons to change. Cite recent changes, distinct
  responsibilities, or test setup that demonstrates the cost.
- Identify repeated logic with real divergence risk. Similar-looking code is not necessarily the
  same concept.
- Introduce an abstraction only after multiple concrete uses establish a stable common behavior.

### Interfaces, data, and state

- Compare public interfaces against declared compatibility policy and consumer usage.
- Check whether one fact has multiple writable representations, cache invalidation paths are
  unclear, or lifecycle states permit invalid combinations.
- Treat migrations and externally visible schema changes as behavior changes; hand them off rather
  than executing them here.

### Errors, concurrency, and resilience

- Inspect swallowed errors, lost context, unbounded work, unsafe shared-state access, retry
  behavior, and cancellation paths.
- Distinguish a behavior-preserving cleanup from a correctness or reliability fix. Record the latter
  as `NEEDS-FIX`.
- Prefer measurements, traces, incidents, failing tests, or reproducible races over hypothetical
  concerns.

### Testability and maintainability

- Prioritize code with both high change frequency and high reasoning cost.
- Look for tests coupled to implementation details, unstable fixtures, hidden time/network/random
  dependencies, and untested seams needed for safe refactoring.
- Use repository-specific complexity trends and review friction. Do not impose universal line,
  branch, coverage, or complexity limits.

### Dependencies and configuration

- Check reproducible installs, lockfiles, unused dependencies, configuration validation, and the
  repository's supply-chain policy.
- Secret exposure or vulnerable dependencies are security findings. Record evidence and hand them
  to a security/fix workflow; do not remediate them as refinements.

## Lens 2: Usability and thoughtfulness

Usability changes often alter observable behavior. Audit them, but execute only internal
refinements that preserve the current contract. Hand desired user-visible changes to a goal
workflow.

### User journeys and states

- Trace representative first-run, normal, empty, loading, error, offline, and recovery paths.
- Use support reports, analytics, usability observations, product requirements, or reproducible
  friction as evidence.
- Check whether progress and results are understandable for the actual duration and task. Avoid
  universal timing thresholds without measurement and product context.

### Accessibility and interaction

- Evaluate the accessibility standard adopted by the product or required by law. Keyboard,
  assistive-technology, zoom, contrast, focus, semantics, and motion checks may provide evidence.
- Treat conformance defects as behavior-changing fixes unless the candidate is demonstrably an
  internal, behavior-preserving cleanup.
- Do not turn optional target sizes, layout preferences, or copy conventions into universal rules.

### Information and language

- Check whether labels, errors, help, navigation, and command output match the user's task and the
  product's established language.
- For internationalized products, inspect formatting, pluralization, translation coverage, fallback
  behavior, text expansion, and bidirectional layout against supported locales.
- Copy or navigation changes are normally observable behavior and should be handed off.

### GUI, CLI, API, and library surfaces

- Respect each surface's documented contract and ecosystem conventions.
- For CLIs, examine stdout/stderr separation, exit status, non-interactive behavior, help, and
  machine-readable output when the project promises them.
- For APIs and libraries, examine error types, compatibility, cancellation, pagination, and
  resource ownership against actual consumers.

## Lens 3: Production readiness and operations

### Security and data safety

- Use the threat model, data classification, trust boundaries, and applicable security baseline.
  Check authorization, injection paths, secret handling, least privilege, input limits, sensitive
  logging, and dependency risk.
- Validate backup and restore claims with available evidence, and inspect retention and deletion
  obligations.
- Record security, privacy, or data-loss findings as `NEEDS-FIX`; this loop does not execute them.

### Operability and observability

- Check whether operators can distinguish healthy, degraded, and failed states using existing logs,
  metrics, traces, health endpoints, and runbooks.
- Prefer signals tied to real user or service objectives. More telemetry is not automatically an
  improvement.
- Look for noisy alerts, missing ownership, ambiguous recovery steps, and unbounded diagnostic data.

### Lifecycle, deployment, and recovery

- Inspect startup, readiness, liveness, shutdown, draining, retry, timeout, rollback, and migration
  behavior against the actual runtime and deployment strategy.
- Use deployment history, incident evidence, load tests, restore drills, or failure injection when
  available.
- Changes to runtime guarantees are behavior changes and require a dedicated workflow.

### Capacity, cost, and compliance

- Compare resource use and limits to measured demand rather than fixed multipliers.
- Check whether service objectives, capacity assumptions, licensing, provenance, and compliance
  controls are documented and testable where the project requires them.
- Treat absent controls as findings, not automatic implementation mandates.

## Lens 4: Refactoring discipline

- Prove behavior preservation with characterization tests or another repository-appropriate oracle
  before changing untested code.
- Keep each candidate atomic and independently reversible. Do not combine unrelated cleanups.
- Prefer direct, local refactoring moves over speculative frameworks or broad rewrites.
- Use incremental migration patterns only when each step preserves the current external contract.
- Add architecture fitness checks when they protect an explicit repository boundary and the value
  exceeds maintenance cost.
- Create an ADR only when existing repository policy requires one. The `.refine-loop/` state files
  are sufficient for loop memory.

## Evidence and stop discipline

- Score only behavior-preserving candidates using `ROI = Impact × Confidence ÷ Effort`.
- Explain scores with repository evidence and uncertainty; do not present the scale as an objective
  quality measurement.
- Churn, complexity, user-path frequency, incidents, support volume, and benchmark data can inform
  impact, but no single signal is decisive.
- Three consecutive rounds without an accepted candidate at or above `theta=2.0` indicate
  diminishing returns at that configured bar, not universal completeness.
