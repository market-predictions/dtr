# Work Package AS-WP-20260723-00 — Standalone Foundation

## Objective

Create an isolated Asia Sweep strategy research foundation inside the DTR repository without modifying the active DTR strategy or its evidence.

## Scope

- dedicated branch and file structure;
- separation contract;
- roadmap, changelog, specification and preregistration;
- NQ and ES manifests;
- standalone signal/event models for AS-A through AS-D;
- deterministic event ledger;
- prefix-replay causality validator;
- separate synthetic test suite;
- independent clean-room review pass;
- draft pull request.

## Out of scope

- P&L backtest;
- parameter optimization;
- DTR/Asia combined portfolio analysis;
- Pine implementation;
- deployment or sizing recommendation.

## Acceptance criteria

1. No active DTR source, test, manifest or evidence file is edited.
2. Asia Sweep does not import or call DTR `generate_signals()`.
3. Tests live outside the default DTR test path.
4. Four variants produce deterministic signal/rejection records.
5. Signal entries occur after the determining five-minute candle closes.
6. A prefix replay can reproduce emitted signals without future bars.
7. NQ is marked development-only while timestamp/roll questions remain unresolved.
8. ES is blocked until data and checksum are registered.
9. Reviewer report identifies unresolved blockers before P&L research.

## Decision

Completion authorizes WP-AS-01 data qualification and event audit. It does not authorize profitability testing on an unqualified ES source or promotion of any variant.
