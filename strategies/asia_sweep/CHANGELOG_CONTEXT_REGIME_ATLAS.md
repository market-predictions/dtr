# Asian Sweep Context and Regime Atlas — Changelog

## v10.2.0 — 2026-07-26

### Changed

- completed the authoritative EURUSD/GBPUSD 2015–2021 atlas;
- evaluated 2,900 T5 events and 106 preregistered context states;
- confirmed that higher-timeframe direction, trend strength, trend change, volatility and causal location produced no passing state after breadth, bootstrap and FDR gates;
- retained `sweep_half_hour::0900_0929` as the sole passing attribution state;
- blocked interactions and router modelling because only one independent factor family passed;
- added the final decision and independent artifact audit;
- closed and released the work package and claim;
- retired the expensive workflow to manual reproduction only.

### Reason

The frozen single-factor gate failed to establish broad regime support. Continuing into interactions would convert weak descriptive variation into post-hoc filter mining.

### Known limitations

- the passing 09:00–09:29 state still had -0.3947R absolute stressed payoff proxy;
- it is a relative attribution effect, not a profitable strategy;
- 2022–2025 cannot serve as untouched validation for this newly isolated time state;
- unchanged future-data or cross-asset replication is required before any further consideration.

### Next

- stop the current higher-timeframe/regime programme;
- preserve the 09:00–09:29 state only as an unvalidated replication hypothesis;
- do not reopen interactions, entry, stop, target, runner or position-management research from this result.

## v10.1.0 — 2026-07-26

### Changed

- reopened the broader higher-timeframe, trend-strength, trend-change, volatility and causal-location roadmap from the validated fingerprint base;
- froze exact D1/W1 direction, slope, efficiency, acceleration/deceleration, volatility percentile, volatility-transition and location definitions;
- added synchronized BID/ASK source loading and Amsterdam daily/weekly context aggregation;
- added the exact frozen T5 population and a conservative stressed remaining-payoff proxy;
- added complete single-factor attribution with pair/year breadth, date-block bootstrap, clustered sign permutation and Benjamini-Hochberg FDR control;
- added a hard interaction gate requiring at least two independent factor families to pass;
- added focused synthetic tests and an isolated authoritative Actions workflow.

### Reason

The failed weekly-profile hypotheses covered only one narrative branch of the broader regime roadmap. This programme tests the remaining causal market-context families without reopening rejected entry, stop, target or runner policies.

### Known limitations

- 2022–2025 were already used in the completed fingerprint validation programme and cannot serve as untouched validation for a newly discovered regime rule;
- the stressed payoff measure is an attribution proxy, not full strategy execution P&L;
- a passing atlas state requires future data or unchanged cross-asset replication before promotion.

### Next

- run the 2015–2021 single-factor atlas;
- freeze at most six non-redundant interactions only if two independent factor families pass;
- otherwise close the programme before interactions and router modelling.
