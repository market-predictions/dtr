# Handover — AS-WP-20260723-01

## Delivered

- exact one-minute interval-integrity model;
- strict Asia-range completeness gate;
- causal pre-signal path gate;
- non-retrospective treatment of future gaps;
- complete-window requirement before `NO_SWEEP` classification;
- strict ZIP/CSV source adapter with explicit schema and checksum contract;
- duplicate and off-grid timestamp rejection;
- event-level integrity metadata;
- complete causal AS-C reference history;
- 25 isolated tests;
- full pytest artifacts in the dedicated workflow;
- original DTR CI and dedicated Asia Sweep CI passing;
- independent published-diff review;
- no P&L, optimization, or DTR/Asia combination.

## Review defects resolved

- removed inherited silent deduplication and final-date deletion;
- removed pytest module-name collision with DTR tests;
- corrected Ruff import formatting;
- improved CI log auditability.

## Not delivered

- qualified ES dataset;
- resolution of NQ bar-label semantics;
- resolution of NQ/ES continuous-contract construction;
- historical event ledgers from raw data;
- manual 50 NQ + 50 ES event audit;
- post-entry execution simulation;
- historical or fresh OOS P&L.

## Decision

`DATA_INTEGRITY_MERGEABLE_EVENT_RESULTS_AND_PNL_BLOCKED`

The code gate may merge. Strategy research may continue only with source registration and event-only audit.

## Next work package

`AS-WP-20260723-02 — Qualified Data Registration and Manual Event Audit`

Required order:

1. register qualified ES path, checksum, source schema, timestamp semantics, and roll method;
2. resolve NQ timestamp labels or preregister both plausible interpretations;
3. register continuous-contract or individual-contract metadata;
4. generate NQ and ES event ledgers without P&L;
5. audit at least 50 events per instrument;
6. correct semantic defects without viewing returns;
7. freeze event specification and ledgers;
8. independently review whether execution integration remains worthwhile.
