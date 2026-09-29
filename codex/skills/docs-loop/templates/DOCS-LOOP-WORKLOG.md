# DOCS-LOOP WORKLOG

> Append-only evidence log for authorized APPLY and OPEN-PRS runs. DRY-RUN emits a report and does not
> create or update this file.

## Run

- state format: 1
- scope: {{SCOPE}}
- canonical scope fingerprint: {{SCOPE_FINGERPRINT}}
- mode: {{MODE}}
- started: {{STARTED_AT}}

## Entries

<!--
Append one real entry after each repository reaches a terminal status. Do not add sample entries, fake PR
URLs, or unresolved placeholders.

Each entry records:
- timestamp and canonical repository path;
- terminal status and non-sensitive reason;
- queried remote, default branch, and pinned base commit;
- isolated branch and preserved/removed worktree path;
- documentation audited and exact files changed;
- each changed claim with affirmative file:line evidence;
- deferred findings with their deferred-record identifiers;
- fresh-review result and every available linter/check command with fresh outcome;
- staged-document regex scan and installed-gitleaks outcome;
- mode-specific deliverable:
  - APPLY: preserved worktree path, no commit or PR;
  - OPEN-PRS: commit identifier, PR URL, and PR-tied checks outcome.

Never record credential values or copy sensitive governing-instruction content.
-->
