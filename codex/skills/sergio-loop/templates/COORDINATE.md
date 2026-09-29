# Coordination Board

> Append-only human-readable coordination log. This board provides memory and communication, not mutual
> exclusion. A claim is valid only while its matching exclusive machine lease in
> `.omc/sergio-loop/leases/` is live and consistent.

## Rules

- Append entries at the bottom. Never edit or delete an earlier entry; append a correction or resolution.
- Every entry uses the complete schema below and a globally unique entry ID.
- Canonical path overlap includes equality and ancestor/descendant relationships.
- Never edit a path with another live owner.
- Shared resources and contract changes require both a board ACK and machine lease `ACKNOWLEDGED` state.
- A stale, missing, expired, rejected, or mismatched lease grants no ownership.

## Log

<!-- Append entries with every field in this stable schema:

### ISO_8601_TIMESTAMP · ENTRY_ID · TYPE

- Owner: UNIQUE_OWNER_ID
- Segment: POSITIVE_INTEGER
- Iteration: NONNEGATIVE_INTEGER
- In reply to: ENTRY_ID_OR_NULL
- Lease ID: LEASE_ID_OR_NULL
- Paths: [CANONICAL_PATHS]
- Resources: [NORMALIZED_RESOURCE_IDS]
- Lease expiry: ISO_8601_TIMESTAMP_OR_NULL
- Lease ACK state: `NOT_REQUIRED|PENDING|ACKNOWLEDGED|REJECTED`
- Message: OBSERVED_FACT_REQUEST_OR_DECISION
- Evidence: OBSERVED_EVIDENCE_OR_NONE

TYPE is one of:

- `JOIN`: register an owner and intended scope; lease fields are null/empty.
- `CLAIM`: announce an already-created live machine lease.
- `ACK`: reply to a pending claim after atomically updating its machine ACK state.
- `ASK`: request work, information, ownership transfer, or current authorization.
- `PROGRESS`: report verified progress under a live lease.
- `RELEASE`: report a machine lease already marked RELEASED.
- `BLOCKED`: report a concrete blocker and its evidence.
- `CORRECTION`: supersede an earlier entry without changing it.

The first entry must be JOIN with observed values. Do not add example, placeholder, or speculative entries.
-->
