# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-12 — E6 portfolio sequencing`

Status: **research complete; independent review passed; publication branch active**

Decision state: `RETAIN_S0_GLOBAL_SEQUENCING`

Base dependency: `DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space execution` remains a stacked draft on PR #11.

## Baseline hierarchy

### Execution regression benchmark

`DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`

- 495 trades;
- 86.004761R net;
- 0.173747R expectancy.

Purpose: detect unintended engine changes.

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

E6 is a research baseline only. It does not replace the control and is not deployable.

## Completed E6 Blocks 0–3

E6's prior-day-extreme exclusion mechanism is `SUPPORTED`. The rejected near-extreme cohort had materially lower expectancy, more stop-first outcomes and fewer target hits. P1–P3, R1–R2 and I1 did not improve the full E6 portfolio; no new filter advanced.

Decision: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.

## Completed Block 4 — Portfolio sequencing

| Arm | Trades | Risk-normalized net R | Expectancy | Max DD | Return/DD | Decision |
|---|---:|---:|---:|---:|---:|---|
| S0 current global | 304 | 48.94R | 0.161R | 8.63R | 5.67 | Retain |
| S1 first per ETH date | 259 | 41.73R | 0.161R | 8.76R | 4.77 | Reject |
| S2 60-minute cooldown | 300 | 47.73R | 0.159R | 8.63R | 5.53 | Reject |
| S3 one-third-risk session sleeves | 310 | 15.58R | 0.151R raw | 3.19R | 4.89 | Reject |

Findings:

- first-trade-only removed 45 trades that earned 7.20R;
- the cooldown removed four trades that earned 1.20R and did not reduce drawdown;
- session sleeves enabled only six extra trades, which lost 2.19R;
- cross-session overlap was rare: 12 trades participated and maximum concurrency was two;
- permanently dividing risk into thirds underused capital and reduced risk-normalized return;
- all three alternatives had negative observed incremental net R versus S0;
- independent reconstruction and deterministic repeat passed.

Decision: retain one global open position at a time. Do not search alternate cooldowns, daily trade limits, sleeve weights or dynamic reallocation on the current sample.

## Next authorized work

Block 5 diagnostic attribution:

- official FOMC announcement dates;
- CPI release dates;
- Employment Situation/NFP dates;
- quarterly equity-index futures expiration and the preceding five business days;
- early-close and shortened-session dates;
- detected contract-roll discontinuity windows.

This block is attribution-only and cannot create a historical exclusion filter.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No E6 threshold change, neighboring-threshold search, weekday/session search, sequencing retune, additional interaction, Pine port, sizing recommendation, leverage increase or deployment is authorized.
