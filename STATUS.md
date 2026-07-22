# DTR Optimization Lab Status

## Current stacked work package

`DTR-CROSSMARKET-WP-20260722-18 — NQ versus USA500 parallel replication framework`

Status: **framework complete; execution, independent review, deterministic repeat and CI pending final publication gate**

Decision state: `PARTIAL_COST_FRAGILE_REPLICATION`

Base dependency: `DTR-ESPROXY-WP-20260722-17 — Dukascopy USA500 proxy qualification` remains a stacked draft on PR #17.

## Baseline hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

### Timing-corrected non-selectable control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy.

### Frozen E6 comparator

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown.

### Current NQ working research baseline

`E6_NO_FOMC_DAY`

- 291 trades;
- 53.483342R net;
- 0.183792R expectancy;
- 9.151061R maximum drawdown;
- 5.844496 return/DD.

## Cross-market framework

The provider-neutral framework now:

- normalizes NQ and Dukascopy USA500 proxy data to canonical bar-open Eastern Time;
- runs original E6 and E6 no-FOMC through one frozen signal/execution contract;
- preserves instrument-specific data-integrity and execution economics;
- reports opportunity, trade, session, year, direction, cost and uncertainty evidence separately;
- prohibits pooled returns and proxy-specific tuning.

## NQ versus USA500 result

| Instrument | Arm | Trades | Net R | Expectancy | Max DD | 2-tick expectancy |
|---|---|---:|---:|---:|---:|---:|
| NQ | E6 | 304 | 48.94R | 0.161R | 8.63R | 0.143R |
| NQ | E6 no-FOMC | 291 | 53.48R | 0.184R | 9.15R | 0.166R |
| USA500 proxy | E6 | 281 | 13.33R | 0.047R | 17.38R | -0.012R |
| USA500 proxy | E6 no-FOMC | 268 | 12.98R | 0.048R | 16.30R | -0.011R |

Decision: the proxy is positive at one tick per side but not robust to two ticks. Classification: `PARTIAL_COST_FRAGILE_REPLICATION`.

## Attribution

- Proxy London: 107 trades, +31.13R, 0.291R expectancy.
- Proxy Asia: 67 trades, -7.23R.
- Proxy New York: 107 trades, -10.57R.
- Proxy E6 date-block 95% expectancy interval: approximately -0.097R to +0.197R.
- The no-FOMC overlay improved NQ by +4.55R but reduced proxy total return by 0.35R after exact resequencing.

No London-only rule, proxy filter or FOMC redefinition is authorized.

## Next evidence gate

- materially longer USA500 proxy replication using the unchanged framework;
- actual contract-audited ES futures data if available;
- qualified fresh post-2025 NQ data;
- materially longer contract-audited NQ history.

## Existing unresolved gates

- authoritative NQ timestamp metadata: `UNRESOLVED`;
- NQ continuous-contract methodology: `UNRESOLVED`;
- qualified fresh NQ OOS comparison: `NOT_RUN`;
- actual ES futures replication: `NOT_RUN`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No proxy-specific threshold, session, weekday, cost selection, FOMC rule change, pooled NQ/proxy portfolio, dynamic sizing, Pine port, live sizing recommendation, leverage increase or deployment is authorized.
