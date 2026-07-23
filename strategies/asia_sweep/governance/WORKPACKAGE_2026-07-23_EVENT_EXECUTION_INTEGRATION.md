# Work Package AS-WP-20260723-05 — Event-to-Execution Integration and Deterministic Replay Gate

**Status:** COMPLETE — exact-head merge gates pending  
**Decision:** `SYNTHETIC_EVENT_EXECUTION_INTEGRATION_FROZEN_REAL_DATA_PNL_BLOCKED`

## Objective

Connect frozen Asia Sweep event records to the frozen synthetic-only execution contract through a separate, deterministic adapter. Use synthetic event packets and synthetic one-minute bars only. Do not enable private proxy/futures execution or real-data P&L.

## Strategic boundary

The event layer determines whether a setup exists. The execution layer determines the outcome of an already-frozen signal. This work package maps immutable event facts into `ExecutionSignal`, but does not alter event eligibility, variant logic, first-sweep ownership, confirmation timing, stop construction or target ratio.

## Frozen integration contract

### Required event fields

A mappable event must contain:

- `instrument`;
- `trade_date`;
- `execution_window`;
- `variant`;
- `status` equal to `SIGNAL`;
- `direction` equal to `1` or `-1`;
- `entry_timestamp`;
- `entry_price_raw`;
- `stop_price_raw`;
- `target_price_raw`.

### One-instrument economics

- Every `IntegrationConfig` is bound to one explicit instrument.
- Every event in a packet must match that instrument.
- Tick size, point value, commission and slippage cannot be inherited silently by another instrument.
- Mixed-instrument packets fail before execution.

### Immutable mapping

- `instrument` must match the configured instrument.
- `direction` maps unchanged.
- `entry_timestamp` becomes `ExecutionSignal.signal_timestamp` after causal conversion to the configured session timezone.
- `stop_price_raw` becomes the fixed execution stop.
- `target_rr` is locked to 2.0.
- `window_end` is derived from the frozen execution-window definition and event trade date using wall-calendar semantics.
- Event input must not be mutated.
- Mapping must not call signal generation or inspect future bars.

### Source-kind and frame-binding policy

- Event packets must be explicitly marked `SYNTHETIC_EVENT_PACKET`.
- Minute frames must retain the frozen execution marker `SYNTHETIC_TEST_FIXTURE`.
- Every minute frame must also carry the stable event key.
- Every minute frame must carry a digest of all execution-relevant event facts.
- Swapped frames or frames created for an earlier payload revision fail before simulation.
- Any unmarked or mismatched event/minute source fails loudly.
- These markers are accidental-use workflow guards, not security boundaries.
- No manifest, CLI or workflow connects registered proxy/futures data in this package.

### Identity and payload policy

The stable event key contains only immutable row identity:

- instrument;
- trade date;
- execution window;
- variant.

A separate event-contract digest contains:

- identity;
- `SIGNAL` status;
- direction;
- canonical session-timezone entry timestamp;
- entry, stop and target expressed in integer ticks;
- frozen 2.0R target ratio.

This separation keeps row identity stable while exposing execution-relevant revisions.

### Price-grid policy

- Synthetic integration is strict-grid only.
- Event entry, stop and target prices must lie exactly on the configured tick grid.
- Every one-minute OHLC value supplied to integrated execution must lie on the same tick grid.
- No rounding, snapping or proxy-to-futures conversion is permitted.
- Off-grid inputs fail loudly.
- A later real-data adapter must preregister its own source-kind and conservative price-normalization policy.

### Event-geometry and time validation

- Long event: `stop < entry < target`.
- Short event: `target < entry < stop`.
- Signal-layer target must equal 2.0R from the event entry and stop within a strict numerical tolerance.
- Risk must exceed one tick.
- Entry timestamp must be timezone-aware and one-minute aligned.
- Local entry date must equal `trade_date`.
- Entry must lie inside its declared half-open London or New York execution window.
- Variant must be one of the four preregistered variants.
- Non-signal, missing, duplicate-key or internally inconsistent rows fail loudly.

### Replay contract

- A synthetic packet maps each event exactly once.
- Execution output retains stable identity, event-contract digest, original event geometry and explicit execution economics.
- Batch replay must equal independent row-by-row replay.
- Reordering input rows must not change per-event outcomes.
- Duplicate event keys are prohibited.
- Missing, orphan or malformed frame-map keys are prohibited.
- Prefix replay must reproduce the same mapped signal and execution outcome once the determining minute is present.
- Event records and minute frames remain unchanged after replay.

## Completed adversarial coverage

1. Long and short event mapping.
2. Wall-calendar London and New York window-end derivation.
3. DST-aware event mapping.
4. Rejection of unmarked event packets and unbound minute frames.
5. Rejection of non-signal rows.
6. Rejection of unknown variants and execution windows.
7. Rejection of missing and non-string identity fields.
8. Rejection of duplicate stable event keys.
9. Rejection of off-grid event prices.
10. Rejection of off-grid one-minute OHLC.
11. Rejection of invalid long/short price geometry.
12. Rejection of a target inconsistent with frozen 2.0R.
13. Rejection of entry timestamps outside the declared window or trade date.
14. Stable event-key construction.
15. Event-contract digest sensitivity to payload changes.
16. One-instrument economics binding.
17. Mixed-instrument packet rejection.
18. Swapped-frame rejection.
19. Same-identity payload-drift rejection.
20. Missing, orphan and malformed frame-map key rejection.
21. Batch replay equals independent row replay.
22. Input order does not change outcomes.
23. Event and minute inputs remain immutable.
24. Prefix replay preserves target and data-gap execution.
25. No active DTR signal function is called.
26. No real/private source adapter exists.

## Prohibited

- private Dukascopy proxy execution;
- CME futures execution;
- real-data P&L, MFE or MAE;
- variant comparison or selection;
- parameter optimization;
- portfolio combination or risk allocation;
- shared DTR execution extraction before locked benchmark replay;
- Pine Script implementation;
- deployment or paper-trading claims.

## Acceptance evidence

- Integration code lives under the standalone Asia Sweep namespace.
- The frozen execution simulator was not weakened or outcome-tuned.
- Strict source-kind, frame-binding and price-grid contracts fail loudly.
- Synthetic batch and independent replay match trade for trade.
- Event identities and outcomes are deterministic under input reordering.
- Event and minute inputs remain immutable.
- Isolated Asia Sweep suite: 185 passed on Python 3.11 and 3.12.
- Repository Ruff passed.
- Full repository tests passed on Python 3.11 and 3.12.
- Clean-room review recorded as `APPROVE_SYNTHETIC_INTEGRATION_FOR_MERGE_REAL_DATA_PNL_BLOCKED`.
- No private data, real execution, P&L, optimization or variant ranking was produced.

## Review corrections

1. Bound each configuration to one instrument after review found that mixed instruments could inherit the same point value and commission schedule.
2. Bound each minute fixture to its event key and payload digest after review found that a generic synthetic marker did not prevent frame swaps.
3. Added a separate event-contract digest so same-identity execution revisions remain visible.
4. Added strict local-date and declared-window membership.
5. Rejected fractional, boolean and non-finite directions.
6. Rejected missing/non-string identities and malformed frame-map keys.
7. Applied the pinned Ruff import order and removed the temporary diagnostic workflow.

## Next gate

Successful merge may authorize a separate proxy execution-source adapter design and synthetic adversarial normalization tests. It does not authorize real-data execution or P&L.

Any future proxy/futures adapter must freeze and independently review:

- source identity and licensing constraints;
- timestamp and bar-label semantics;
- price normalization and tick translation;
- instrument-specific point value, commission, spread and slippage;
- activity and missing-data behavior after entry;
- unresolved-exit policy;
- proxy-versus-futures limitations;
- deterministic replay and audit outputs.
