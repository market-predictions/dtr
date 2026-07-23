# Work Package AS-WP-20260723-05 — Event-to-Execution Integration and Deterministic Replay Gate

## Objective

Connect frozen Asia Sweep event records to the frozen synthetic-only execution contract through a separate, deterministic adapter. Use synthetic event packets and synthetic one-minute bars only. Do not enable private proxy/futures execution or real-data P&L.

## Strategic boundary

The event layer determines whether a setup exists. The execution layer determines the outcome of an already-frozen signal. This work package may map immutable event facts into `ExecutionSignal`, but may not alter event eligibility, variant logic, first-sweep ownership, confirmation timing, stop construction or target ratio.

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

### Immutable mapping

- `instrument` maps unchanged.
- `direction` maps unchanged.
- `entry_timestamp` becomes `ExecutionSignal.signal_timestamp`.
- `stop_price_raw` becomes the fixed execution stop.
- `target_rr` is locked to 2.0.
- `window_end` is derived from the frozen execution-window definition and the event trade date using wall-calendar semantics.
- Event input must not be mutated.
- Mapping must not call signal generation or inspect future bars.

### Source-kind policy

- Event packets must be explicitly marked `SYNTHETIC_EVENT_PACKET`.
- Minute frames must retain the frozen execution marker `SYNTHETIC_TEST_FIXTURE`.
- Any unmarked event or minute source fails loudly.
- This marker is an accidental-use workflow guard, not a security boundary.
- No manifest, CLI or workflow may connect registered proxy/futures data in this package.

### Price-grid policy

- Synthetic integration is strict-grid only.
- Event entry, stop and target prices must lie exactly on the configured tick grid.
- Every one-minute OHLC value supplied to integrated execution must lie exactly on the same tick grid.
- No rounding, snapping or proxy-to-futures conversion is permitted.
- Off-grid inputs fail loudly.
- A later real-data adapter must preregister its own source-kind and conservative price-normalization policy.

### Event-geometry validation

- Long event: `stop < entry < target`.
- Short event: `target < entry < stop`.
- Signal-layer target must equal 2.0R from the event entry and stop within a strict numerical tolerance.
- Entry timestamp must precede the derived window end.
- Variant must be one of the four preregistered variants.
- Non-signal, missing, duplicate-key or internally inconsistent rows fail loudly.

### Replay contract

- A synthetic packet maps each event exactly once.
- Execution output retains a stable event key and all original identity fields.
- Batch replay must equal independent row-by-row replay.
- Reordering input rows must not change per-event outcomes.
- Duplicate event keys are prohibited.
- Prefix replay must reproduce the same mapped signal and execution outcome once the determining minute is present.
- Event records and minute frames remain unchanged after replay.

## Required adversarial tests

1. Long and short event mapping.
2. Wall-calendar London and New York window-end derivation.
3. DST-aware event mapping.
4. Rejection of unmarked event packets and unmarked minute frames.
5. Rejection of non-signal rows.
6. Rejection of unknown variants and execution windows.
7. Rejection of missing required fields.
8. Rejection of duplicate stable event keys.
9. Rejection of off-grid event prices.
10. Rejection of off-grid one-minute OHLC.
11. Rejection of invalid long/short price geometry.
12. Rejection of a target inconsistent with frozen 2.0R.
13. Rejection of entry timestamps at or after window end.
14. Stable event-key construction.
15. Batch replay equals independent row replay.
16. Input order does not change outcomes.
17. Event and minute inputs remain immutable.
18. Prefix replay preserves mapping and exit.
19. No active DTR signal function is called.
20. No real/private source adapter exists.

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

## Acceptance criteria

1. Integration code lives under the standalone Asia Sweep namespace.
2. The frozen execution simulator is not weakened or outcome-tuned.
3. Strict source-kind and price-grid contracts fail loudly.
4. Synthetic batch and independent replay match trade for trade.
5. Event identities and outcomes are deterministic under input reordering.
6. Event and minute inputs remain immutable.
7. Existing event audits remain unchanged and no-P&L.
8. Isolated Asia Sweep tests pass on Python 3.11 and 3.12.
9. Original repository CI remains green.
10. Independent same-session clean-room review is documented honestly.

## Next gate

Successful completion may authorize a separate controlled-development adapter design. It does not authorize real-data execution or P&L. Any future proxy/futures adapter must freeze source identity, tick-grid normalization, cost validity and unresolved-data behavior before connecting private data.