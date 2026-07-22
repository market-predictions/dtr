# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-16 — E6 no-FOMC risk recalibration`

Status: **complete; independent review and deterministic repeat passed**

Decision state: `NO_FOMC_RISK_RECALIBRATION_COMPLETE_NO_SIZING_AUTHORIZATION`

Base dependency: `DTR-NQ-WP-20260722-15 — Promote E6 no-FOMC working baseline` remains a stacked draft on PR #15.

## Baseline hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

### Mandatory non-selectable control

`DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`

- 477 trades;
- 42.577515R net;
- 0.089261R expectancy;
- 16.426493R maximum drawdown.

### Frozen E6 comparator

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown.

### Current working research baseline

`E6_NO_FOMC_DAY`

- 291 trades;
- 53.483342R net;
- 0.183792R expectancy;
- 9.151061R maximum drawdown;
- 5.844496 return/DD.

## No-FOMC risk recalibration

Observed $100,000 account under normal costs:

- 0.50% risk: $129,885 final equity; 4.51% maximum drawdown.
- 1.00% risk: $166,725 final equity; 8.87% maximum drawdown.
- 1.50% risk: $211,540 final equity; 13.09% maximum drawdown.

Observed account under severe four-tick-per-side costs:

- 0.50% risk: $120,388 final equity; 5.10% maximum drawdown.
- 1.00% risk: $143,251 final equity; 10.01% maximum drawdown.
- 1.50% risk: $168,498 final equity; 14.73% maximum drawdown.

Resampled conclusion:

- 0.50% remains the most resilient tested envelope.
- 1.00% remains the middle paper-research envelope; under severe costs, 20% drawdown probability is approximately 7.1–10.1%.
- 1.50% remains aggressive; under severe costs, 20% drawdown probability is approximately 36.6–42.9% and 30% drawdown probability is approximately 5.6–8.2%.

No live sizing recommendation follows.

## Next evidence gate

- qualify Dukascopy `USA500.IDX/USD` as an S&P 500 CFD proxy, not ES futures;
- audit historical depth, sessions, timestamps, missing bars, spreads, and discontinuities before performance inspection;
- then run unchanged original E6 and E6 no-FOMC replication side by side;
- retain qualified fresh NQ and longer contract-audited NQ as parallel priorities.

## Existing unresolved gates

- authoritative NQ timestamp metadata: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- qualified fresh OOS comparison: `NOT_RUN`;
- Dukascopy USA500 proxy qualification: `NOT_RUN`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No additional FOMC buffer search, risk-fraction optimization, dynamic sizing, ES-proxy parameter adaptation, Pine port, live sizing recommendation, leverage increase, or deployment is authorized.
