# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-13 — E6 event, holiday and rollover attribution`

Status: **research complete; independent review and deterministic repeat passed**

Decision state: `RETAIN_E6_NO_EVENT_EXCLUSION_WATCH_FOMC_PRE_AND_ROLL_EXPIRY_OVERLAP`

Base dependency: `DTR-NQ-WP-20260722-12 — E6 portfolio sequencing` remains a stacked draft on PR #12.

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

### Working advanced-test baseline

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown;
- 5.668942 return/DD.

E6 remains research-only and unchanged.

## Completed advanced blocks

- Blocks 0–3: E6 mechanism supported; no additional path or reward-space filter advanced.
- Block 4: retain current one-open-position global sequencing.
- Block 5: official event, holiday, expiration and rollover attribution complete.

## Block 5 findings

- FOMC day: 14 trades, -5.56R. Weakness was concentrated before the 14:00 ET statement: nine trades, -7.62R.
- CPI day: 18 trades, +1.76R; no clear adverse pattern.
- NFP day: nine trades, +1.37R; insufficient sample and no clear adverse pattern.
- Expiration week: 27 trades, -2.09R.
- Roll window: 25 trades, -0.58R.
- The expiration and roll weakness came from the same 18-trade intersection, which lost 5.20R. Expiration-only and roll-only cohorts were positive.
- No customary roll-date trades occurred because roll dates are Mondays and E6 trades Tuesday–Friday.
- No roll window exceeded the frozen 99th-percentile maintenance-gap threshold.
- Independent reconstruction and deterministic repeat passed.

Decision: retain E6 unchanged. Preserve FOMC-pre and expiration/roll-overlap only as fixed risk-watch cohorts for longer or fresh data. Do not create an event exclusion from 2023–2025.

## Next authorized work

Block 6 fixed-fraction equity and execution-cost stress for unchanged E6:

- 0.50%, 1.00% and 1.50% current-equity risk;
- normal, two-tick-per-side and four-tick-per-side execution;
- date-block and month-block resampling;
- final-equity, drawdown, losing-streak and time-under-water distributions.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No E6 threshold change, event-window search, event exclusion, weekday/session search, sequencing retune, additional interaction, Pine port, sizing recommendation, leverage increase or deployment is authorized.
