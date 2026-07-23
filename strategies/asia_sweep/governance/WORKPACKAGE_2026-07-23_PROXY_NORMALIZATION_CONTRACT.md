# Work Package AS-WP-20260723-06 — Proxy Normalization Contract

**Status:** COMPLETE — exact-head merge gates pending  
**Decision:** `SYNTHETIC_PROXY_NORMALIZATION_FROZEN_PRIVATE_EXECUTION_AND_PNL_BLOCKED`

## Objective

Freeze a deterministic, explicitly pessimistic adapter from synthetic Dukascopy-style index-CFD proxy events and one-minute BID bars on a `0.001` source grid into the frozen instrument-specific `0.25` Asian Sweep integration grid.

This package is synthetic-only. It does not load private data, run real execution, calculate P&L, select variants or modify active DTR behavior.

## Frozen contract

### Source identity

- Source kind: `SYNTHETIC_DUKASCOPY_INDEX_CFD_PROXY_FIXTURE`.
- Every configuration is bound to one research instrument, one exact provider source instrument and BID side.
- Tests use `usatechidxusd` for NQ-like fixtures and `usa500idxusd` for ES-like fixtures.
- Only policy `DIRECTIONAL_PESSIMISTIC_V1` is accepted.
- Event and frame markers include source instrument, BID side, stable event key and canonical source-event digest.

### Source validation

- Source entry, stop and OHLC must be positive, finite and exactly aligned to the source quote increment.
- Source timestamps must be timezone-aware, minute aligned and unique.
- Raw OHLC geometry must be valid.
- Missing timestamps remain missing and activity flags remain unchanged.
- Rows before entry or after execution-window end fail.
- Execution tick must be an exact integer multiple of source quote increment.
- Decimal arithmetic defines every grid operation.

### Event validation and normalization

Raw event requirements:

- status `SIGNAL`;
- direction exactly `1` or `-1`;
- one of AS-A through AS-D;
- timestamp inside the declared half-open window and on the declared local trade date;
- positive risk and correct long/short geometry;
- canonical 2.0R target from source entry and stop.

Entry and stop are market-observed and remain strict-grid. The derived target may contain arithmetic noise only up to one-millionth of a source increment; canonical and reported target values are retained separately.

Long normalization:

- entry and stop: ceiling to execution grid;
- target: exact 2.0R from normalized entry and stop.

Short normalization:

- entry and stop: floor to execution grid;
- target: exact 2.0R from normalized entry and stop.

Normalized risk must exceed one execution tick.

### Minute bars

Long:

- entry open ceiling;
- later opens, highs, lows and closes floor.

Short:

- entry open floor;
- later opens, highs, lows and closes ceiling.

Favorable extremes therefore move inward and adverse extremes outward. OHLC repair is limited to including normalized open and close inside the high/low envelope.

### Audit and binding

The adapter retains:

- raw and normalized event prices;
- reported and canonical source target;
- raw and normalized OHLC;
- source instrument and BID side;
- source increment and execution tick;
- envelope-repair flags;
- source-event, source-frame and normalization digests.

Normalized outputs are sealed to the frozen WP5 event key and event-contract digest. The adapter never calls execution automatically.

## Review corrections

1. Added exact provider-instrument and BID-side binding.
2. Locked the policy version rather than allowing hidden alternatives.
3. Separated derived-target arithmetic noise from strict observed-price grid validation.
4. Retained reported and canonical source targets.
5. Corrected an off-grid fixture whose float literal canonicalized to the on-grid value.
6. Applied pinned Ruff import ordering and removed all temporary workflows.

## Validation

- Repository Ruff: passed.
- Full repository tests: passed on Python 3.11 and 3.12.
- Isolated Asian Sweep suite: 223 passed on Python 3.11 and 3.12.
- Source-symbol, BID-side and policy locks passed.
- Decimal rounding, long/short pessimism and risk-collapse tests passed.
- Timestamp, gap and activity preservation passed.
- Wrong-source, wrong-side, swapped-frame and stale-payload rejection passed.
- Source-row order invariance and digest determinism passed.
- Normalized outputs satisfied the frozen WP5 contract.
- Review verdict: `APPROVE_SYNTHETIC_PROXY_NORMALIZATION_FOR_MERGE_PRIVATE_EXECUTION_BLOCKED`.
- No private data, real execution, P&L, optimization or variant ranking was produced.

## Prohibited

- private Dukascopy loading or normalization in this package;
- CME futures loading or execution;
- real-data P&L, MFE or MAE;
- variant ranking or parameter optimization;
- portfolio combination;
- active DTR changes or shared execution extraction;
- Pine Script or deployment claims.

## Next gate

After merge, a separate private normalization-audit package may generate deterministic raw-versus-normalized evidence packets. It must not call execution or produce P&L, must remove private source data before artifact upload, and must complete programmatic and manual audit before any real execution package is considered.
