# docs-loop staleness signals

Audit documentation against the pinned commit from the repository's queried default branch. Auditing is
read-only in every mode; editing starts only after findings are independently confirmed and the invocation
authorizes APPLY.

## Evidence rule

Search absence is not contradiction. A grep miss, an unfamiliar symbol, or an old timestamp can justify
more investigation, but cannot justify an edit.

Use `WRONG` or `STALE` only with affirmative contradictory evidence:

- code or configuration defines a different current value;
- generated CLI/API output differs from the documented command or signature;
- Git tracks a replacement path or module and current references use it;
- authoritative project metadata names a different supported version or default;
- a relative link or anchor is deterministically unresolved;
- a diagram contradicts the current tracked structure or fails to parse.

If the evidence only fails to confirm the claim, use `UNKNOWN` and defer. Never delete, soften, or rewrite a
claim solely because no supporting grep hit was found.

## Signals

### Factual drift

Check concrete, externally useful claims:

- ports, environment variable names, defaults, and config keys;
- CLI flags, subcommands, examples, and exit behavior;
- API routes, parameters, signatures, and response fields;
- file paths, package/module names, runtime requirements, and supported versions;
- install, build, test, migration, and deployment commands.

A conflicting current definition is `WRONG`. A true value tied to an obsolete interface is `STALE`.
Ambiguous ownership or multiple active definitions is `UNKNOWN`.

### Structural drift

Compare architecture and component descriptions with tracked packages, modules, entry points, and
dependency configuration. A rename or replacement requires evidence connecting the old and new structures;
a missing old path by itself is not enough.

Check every Mermaid block in a changed file for both semantic consistency and parser validity when a parser
is available.

### Dead references

Check all tracked Markdown, MDX, reStructuredText, and AsciiDoc files in scope. Do not skip arbitrary
directories or filenames. Resolve relative links from the source document, validate local anchors, and
separate deterministic local failures from transient network failures.

Use the null-delimited `find` workflow in
[safety-contract.md](safety-contract.md#gate-7--portable-link-checks). A missing local tracked target is
`WRONG`; an unavailable external URL is `UNKNOWN` unless authoritative evidence confirms removal or
replacement.

### Coverage gaps

Use `MISSING` only when the explicit scope requires documentation for a shipped public surface and no
current documentation covers it. New narrative, roadmap, legal, licensing, positioning, or security-posture
text requires human intent and is `UNKNOWN`/`DEFERRED`.

### Age and churn

Documentation older than related code, recent symbol renames, and high code churn are prioritization
signals only. They are never proof and never permit extrapolation to another repository.

## Finding format

Return one row per examined claim:

```text
doc:line | claim | affirmative evidence file:line | verdict | proposed action | confidence
```

Allowed verdicts:

- `MATCHES`: affirmative evidence agrees; leave unchanged.
- `STALE`: affirmative evidence shows an obsolete interface or structure.
- `WRONG`: affirmative evidence directly contradicts the claim.
- `MISSING`: explicit scope requires coverage for a confirmed shipped public surface.
- `UNKNOWN`: evidence is absent, ambiguous, transient, or intent-dependent; defer.

Confidence is `high`, `medium`, or `low`. Only high-confidence `STALE`, `WRONG`, or explicitly scoped
`MISSING` findings may become edits. A fresh reviewer must reproduce the evidence after editing.

## Dry-run report

For every repository, report:

- pinned default branch and commit;
- documentation examined and tools available;
- each finding with affirmative evidence or the reason it is `UNKNOWN`;
- proposed file-level edits without applying them;
- deferred and blocked items;
- whether APPLY or OPEN-PRS would be required next.

The report must state that no tracked or state files, commits, pushes, or PRs were created. It must also
report whether temporary audit storage was removed or preserved for an actionable finding. It is not a PR
and must not include fake links or unresolved placeholder entries.
