# Work Package AS-WP-20260723-06 — Proxy Normalization Contract and Synthetic Source Adapter

## Objective

Freeze and implement a deterministic, explicitly pessimistic adapter from synthetic Dukascopy-style index-CFD proxy events and one-minute bid bars into the already-frozen event-to-execution integration contract.

This package uses synthetic proxy fixtures only. It must not connect private Dukascopy data, calculate real proxy/futures P&L, select variants or modify active DTR behavior.

## Strategic problem

The registered proxy snapshots expose prices at an observed quote increment of `0.001`, while the intended futures-like execution grid is `0.25`. Raw proxy prices therefore cannot enter the strict execution adapter directly.

A valid source adapter must distinguish:

- provider quote precision from executable futures tick size;
- signal geometry from actual entry fills;
- entry-side and exit-side adverse rounding;
- favorable and adverse intrabar extremes;
- event identity from normalization-policy identity;
- proxy evidence from CME futures evidence.

## Frozen candidate policy for review

### Source boundary

- Accepted source kind: `SYNTHETIC_DUKASCOPY_INDEX_CFD_PROXY_FIXTURE` only.
- Source prices must be positive, finite and exactly aligned to the configured source quote increment.
- Source timestamps must be timezone-aware, one-minute aligned and unique.
- Source OHLC invariants must hold before normalization.
- Activity flags are preserved exactly.
- No private data loader, manifest runner or workflow connection is allowed in this package.

### Grid relationship

- `source_quote_increment` must be positive and finite.
- `execution_tick_size` comes from the frozen `ExecutionConfig`.
- The execution tick must be an exact integer multiple of the source quote increment.
- Decimal arithmetic is required for floor/ceiling operations; binary-float rounding may not define policy.

### Event normalization

The raw proxy event must first be internally consistent at source precision:

- status is `SIGNAL`;
- direction is exactly `1` or `-1`;
- raw event entry, stop and target lie on the source grid;
- raw long geometry is `stop < entry < target`;
- raw short geometry is `target < entry < stop`;
- raw target equals 2.0R from raw entry and stop within source-grid tolerance;
- event timestamp and declared window remain unchanged.

Direction-aware event normalization:

- long event entry: ceiling to execution grid;
- long protective stop: ceiling to execution grid;
- short event entry: floor to execution grid;
- short protective stop: floor to execution grid;
- normalized risk must exceed one execution tick;
- normalized event target is recomputed at exactly 2.0R from normalized event entry and normalized stop;
- the raw target is retained only as audit evidence;
- no nearest-price rounding or favorable snapping is permitted.

### Minute-bar normalization

For a long event:

- entry-minute open: ceiling to execution grid;
- later opens: floor to execution grid;
- highs: floor to execution grid so favorable excursions are not overstated;
- lows: floor to execution grid so adverse excursions are not understated;
- closes: floor to execution grid.

For a short event:

- entry-minute open: floor to execution grid;
- later opens: ceiling to execution grid;
- highs: ceiling to execution grid so adverse excursions are not understated;
- lows: ceiling to execution grid so favorable excursions are not overstated;
- closes: ceiling to execution grid.

After directional normalization, OHLC geometry may be repaired only to include the normalized open and close inside the normalized high/low envelope. The repair may not add a more favorable excursion than the minimum required for valid OHLC.

### Time and horizon policy

- The normalized frame may contain only timestamps from the frozen entry timestamp through the exact execution-window-end timestamp, inclusive.
- Rows before entry or after window end fail loudly.
- Missing timestamps remain missing; the adapter may not fill them.
- Inactive quotes remain inactive; the adapter may not convert them into tradable bars.
- Timestamp identity and activity status are preserved exactly.

### Binding and audit policy

- Raw synthetic proxy event and frame must be explicitly marked and bound to one another.
- The normalized event receives the existing stable event identity plus a separate normalization digest.
- The normalization digest includes source increment, execution tick, policy version, direction and raw event geometry.
- The normalized minute frame is bound to the normalized event using the frozen WP5 event key and event-contract digest.
- Output retains raw and normalized event prices and raw/normalized OHLC columns for audit.
- The normalization adapter must not call the execution simulator automatically.

### Interpretation

This policy is a conservative proxy-normalization stress scenario. It is not a reconstruction of CME trades, bid/ask, roll behavior or exchange fills. Passing this package does not establish that the proxy is a valid futures execution source.

## Required adversarial tests

1. Exact Decimal floor and ceiling at execution-grid boundaries.
2. Rejection when execution tick is not an integer multiple of source increment.
3. Rejection of unmarked synthetic proxy events or frames.
4. Rejection of non-finite, non-positive or off-source-grid prices.
5. Rejection of duplicate, naïve or off-minute timestamps.
6. Rejection of invalid raw OHLC.
7. Rejection of invalid raw long/short event geometry.
8. Rejection of raw target inconsistent with 2.0R.
9. Long event entry/stop normalization.
10. Short event entry/stop normalization.
11. Risk-collapse rejection after normalization.
12. Long entry-minute and later-open directional treatment.
13. Short entry-minute and later-open directional treatment.
14. Favorable-extreme inward and adverse-extreme outward invariants.
15. Minimal OHLC-envelope repair.
16. Exact timestamp and activity preservation.
17. Missing timestamps remain missing.
18. Rejection of rows before entry or after window end.
19. Raw event/frame binding and swapped-frame rejection.
20. Deterministic normalization digest.
21. Output event and minute frame satisfy frozen WP5 integration contracts.
22. Reordering source rows does not change normalized output.
23. Raw inputs remain immutable.
24. No private data loader or active DTR signal function is called.
25. No real-data execution or P&L path exists.

## Prohibited

- private Dukascopy proxy loading;
- CME futures loading or execution;
- real-data P&L, MFE or MAE;
- variant comparison or optimization;
- parameter search over normalization rules;
- portfolio combination;
- shared DTR execution extraction;
- Pine Script implementation;
- deployment or paper-trading claims.

## Acceptance criteria

1. Adapter lives under the standalone Asia Sweep namespace.
2. Policy uses deterministic Decimal arithmetic.
3. Directional pessimism is explicit and testable.
4. Source timestamps, gaps and activity are not repaired.
5. Normalized outputs pass the frozen WP5 event/frame contracts.
6. Raw and normalized evidence remain auditable.
7. Existing event and execution semantics remain unchanged.
8. Isolated Asia Sweep tests pass on Python 3.11 and 3.12.
9. Original repository CI remains green.
10. Unchanged private event-audit stability remains green and no-P&L.
11. Independent same-session clean-room review is documented honestly.

## Next gate

After merge, a separate work package may generate private normalization-only audit packets for a deterministic event sample. That later package must still prohibit execution outcomes and P&L until the normalized source evidence is manually and programmatically audited.
