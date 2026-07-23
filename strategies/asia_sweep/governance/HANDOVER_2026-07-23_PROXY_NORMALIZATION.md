# Handover — Proxy Normalization Contract

**Date:** 2026-07-23  
**Work package:** `AS-WP-20260723-06`  
**Branch:** `agent/asia-sweep-proxy-normalization-contract`  
**Pull request:** `#34`

## Delivered

- Added `src/dtr_lab/strategies/asia_sweep/proxy_normalization.py`.
- Added a deterministic synthetic Dukascopy-style proxy normalization contract.
- Added exact provider-instrument and BID-side source binding.
- Added Decimal source-grid validation and floor/ceiling normalization.
- Added directionally pessimistic event and one-minute bar normalization.
- Added source-event, source-frame and normalization digests.
- Added raw-versus-normalized audit columns and OHLC-envelope repair flags.
- Added compatibility binding to the frozen WP5 event-to-execution integration contract.
- Added adversarial proxy-normalization tests.
- Added independent same-session clean-room review.

## Frozen source contract

### Supported source kind

`SYNTHETIC_DUKASCOPY_INDEX_CFD_PROXY_FIXTURE`

This is a workflow guard for synthetic fixtures only. It is not a security boundary and does not authorize loading private provider data.

### Source identity

Each configuration is bound to:

- one Asian Sweep instrument;
- one exact provider source instrument;
- BID price side only;
- one source quote increment;
- one instrument-specific execution configuration;
- policy `DIRECTIONAL_PESSIMISTIC_V1` only.

Tests use:

- NQ-like integration economics with source `usatechidxusd`;
- ES-like integration economics with source `usa500idxusd`.

### Grid relationship

- Source quote increment defaults to `0.001`.
- Frozen execution tick is supplied by `ExecutionConfig` and is `0.25` in the proxy manifests.
- Execution tick must be an exact integer multiple of source quote increment.
- Decimal arithmetic defines all grid checks and floor/ceiling operations.

## Frozen event normalization

Raw market-observed event entry and stop must be positive, finite and exactly source-grid aligned.

The derived raw 2.0R target may contain only insignificant arithmetic noise: at most one-millionth of a source increment from the canonical Decimal target. The reported and canonical values are retained separately.

### Long

- normalized event entry: ceiling to execution grid;
- normalized protective stop: ceiling to execution grid;
- normalized target: exact 2.0R from normalized entry and stop.

### Short

- normalized event entry: floor to execution grid;
- normalized protective stop: floor to execution grid;
- normalized target: exact 2.0R from normalized entry and stop.

Normalized risk must exceed one execution tick.

## Frozen bar normalization

### Long

- entry-minute open: ceiling;
- later opens: floor;
- highs: floor;
- lows: floor;
- closes: floor.

### Short

- entry-minute open: floor;
- later opens: ceiling;
- highs: ceiling;
- lows: ceiling;
- closes: ceiling.

OHLC envelope repair is limited to including normalized open and close inside the normalized high/low. It may not add a more favorable excursion beyond that minimum.

## Time, gap and activity policy

- Source timestamps must be timezone-aware, one-minute aligned and unique.
- Timestamps are converted causally to the session timezone.
- Rows before event entry or after execution-window end fail.
- Missing timestamps remain missing.
- Inactive rows remain inactive.
- No forward-fill, interpolation or synthetic tradable row is created.
- Raw invalid OHLC fails before normalization.

## Audit identity

The adapter records:

- stable event key from WP5;
- canonical source-event digest;
- raw source-frame digest;
- normalization-policy digest;
- source instrument;
- BID side;
- source quote increment;
- execution tick;
- raw source event prices;
- canonical and reported source target;
- raw source OHLC;
- normalized OHLC;
- high/low envelope-repair flags.

Normalized event/frame outputs are sealed to the frozen WP5 event key and event-contract digest.

## Review corrections

1. Bound event and frame fixtures to exact provider source instrument and BID price side.
2. Locked normalization policy to `DIRECTIONAL_PESSIMISTIC_V1` rather than allowing arbitrary policy strings.
3. Separated derived-target arithmetic noise from strict market-price source-grid validation.
4. Retained both reported and canonical source targets for audit.
5. Corrected one off-grid test fixture whose Python float literal canonicalized back to the on-grid value.
6. Applied the pinned Ruff import order exactly and removed all temporary diagnostic/correction workflows.

## Validation

Reviewed implementation gates:

- repository Ruff: passed;
- repository tests Python 3.11: passed;
- repository tests Python 3.12: passed;
- isolated Asian Sweep tests Python 3.11: passed;
- isolated Asian Sweep tests Python 3.12: passed;
- isolated suite: 223 passed;
- clean-room verdict: `APPROVE_SYNTHETIC_PROXY_NORMALIZATION_FOR_MERGE_PRIVATE_EXECUTION_BLOCKED`.

Final exact-head repository CI, isolated CI and unchanged private NQ/ES no-P&L event-audit stability remain required after governance closure before merge.

## Explicitly not delivered

- no private Dukascopy loading;
- no private normalization packet;
- no CME futures normalization or execution;
- no real-data execution, P&L, MFE or MAE;
- no variant ranking or optimization;
- no portfolio combination;
- no active DTR changes;
- no Pine Script or deployment work.

## Next authorized package

A separate private normalization-audit work package may:

- download the registered private proxy artifact through a protected workflow;
- select a deterministic event sample;
- extract raw one-minute paths from entry through window end;
- generate raw-versus-normalized evidence packets;
- independently verify digests, adjustments and source preservation;
- remove all private source data before artifact upload.

That package must not call the execution simulator or produce P&L.
