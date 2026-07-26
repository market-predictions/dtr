# Asian Sweep Context and Regime Atlas — Status

Updated: 2026-07-26

## Current state

`COMPLETE_STOPPED_BEFORE_INTERACTIONS`

## Binding decision

`FAIL_SINGLE_FACTOR_ATLAS_STOP_BEFORE_INTERACTIONS`

## Completed

- programme and exact factor definitions frozen before outcomes;
- work package and claim completed and released;
- causal BID/ASK, daily, weekly and event-context engine implemented;
- exact frozen T5 population and stressed payoff proxy implemented;
- complete single-factor bootstrap, clustered sign-permutation and FDR atlas executed;
- 2,900 EURUSD/GBPUSD events and 106 context states evaluated;
- both pair ledgers, pooled decision and independent artifact audit completed;
- general repository CI and isolated Asia Sweep CI passed.

## Result

- no higher-timeframe direction state passed;
- no trend-strength or trend-change state passed;
- no volatility state passed;
- no causal-location state passed;
- `sweep_half_hour::0900_0929` was the sole passing attribution state;
- its relative economic effect was positive and broad, but absolute stressed payoff remained -0.3947R;
- only one independent family passed, so interactions and router modelling remained closed.

## Remaining hypothesis

The 09:00–09:29 timing state may be retained only as an unchanged future-data or cross-asset replication hypothesis. It is not an executable strategy and is outside the completed higher-timeframe/regime programme.

## Protected boundaries

- no failed weekly-profile rescue;
- no entry, stop, target, runner or position-structure search;
- no reinterpretation of 2022–2025 as untouched validation;
- no Pine or deployment work.
