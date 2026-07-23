# Handover — AS-WP-20260723-04

## Delivered

- isolated one-minute execution simulator under the standalone Asia Sweep namespace;
- explicit synthetic-source opt-in guard;
- immutable execution signal, configuration and outcome models;
- exact next-minute-open entry semantics;
- adverse directional entry, stop and market-exit slippage;
- fixed signal-layer stop and actual-fill 2.0R target construction;
- conservative stop-first same-minute collision handling;
- long/short stop-gap and target-gap symmetry;
- missing-minute liquidation at the first subsequent active quote;
- 10/11-minute source-inactivity boundary handling;
- first-unsafe-condition precedence for stale versus later missing data;
- exact execution-window-end time exits;
- unresolved outcomes without manufactured returns;
- separate commission and synthetic net-R arithmetic;
- prefix replay validation;
- strict duplicate, off-grid, non-finite, invalid-OHLC and timezone-awareness validation;
- synthetic adversarial suite covering 35 direct execution cases plus the existing Asia Sweep suite;
- no real-data adapter, P&L workflow, DTR coupling or market-data publication.

## Validation

- isolated Asia Sweep suite: `146 passed` on Python 3.11;
- isolated Asia Sweep suite: `146 passed` on Python 3.12;
- repository Ruff passed;
- full repository tests passed on Python 3.11 and 3.12;
- branch comparison changes only standalone Asia Sweep execution, tests and governance;
- execution source contains no call to `generate_signals()` or `dtr_lab.research.engine`;
- unmarked frames are rejected as non-synthetic;
- no manifest, CLI or workflow calls the execution simulator with private proxy/futures data;
- no real-data P&L, optimization or variant selection was performed.

## Review corrections

- corrected two adversarial fixtures that did not isolate the intended risk/stale thresholds;
- applied pinned Ruff import ordering exactly and removed the temporary diagnostic workflow;
- added finite/OHLC and clock-compatibility validation;
- prevented missing-data liquidation on inactive carry-forward quotes;
- froze first-unsafe-condition ownership when stale activity precedes a missing minute;
- locked the target ratio to the preregistered 2.0R.

## Decision

`SYNTHETIC_NEUTRAL_EXECUTION_FROZEN_REAL_DATA_PNL_BLOCKED`

The package is mergeable after exact-head CI and unchanged event-audit stability gates pass. It does not authorize execution on registered proxy data or futures data.

## Not delivered

- event-ledger-to-execution adapter;
- development-period proxy/futures execution;
- real-data P&L, MFE or MAE;
- portfolio-level NQ/ES exposure constraints;
- proxy-to-futures price-grid normalization;
- CME contract/roll/cost/fill validation;
- locked DTR benchmark replay;
- DTR/Asia diversification analysis;
- historical validation or fresh OOS;
- Pine Script implementation;
- deployment or paper-trading recommendation.

## Next work package

`AS-WP-20260723-05 — Event-to-Execution Integration and Deterministic Replay Gate`

Required order:

1. define the immutable mapping from event-ledger fields into `ExecutionSignal`;
2. add explicit price-grid/rounding and source-kind policies;
3. keep the synthetic simulator unchanged and wrap it through a separately reviewed adapter;
4. replay deterministic synthetic event packets trade for trade;
5. prove signal/event ledgers remain unchanged;
6. add portfolio-independent execution summaries without selecting a variant;
7. keep real-data execution and P&L disabled until the integration package merges;
8. if any shared DTR utility is proposed, reproduce the locked DTR benchmark before extraction.
