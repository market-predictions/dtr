# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-10 — E6 advanced test framework and preregistration`

Status: **framework frozen; execution not started**

Decision state: `FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`

Base dependency: `DTR-NQ-WP-20260722-09 — Monday inclusion × Asia exclusion` remains a stacked draft on PR #9.

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

Purpose: remain visible beside every E6-derived result.

### Working advanced-test baseline

`E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME`

- 304 trades;
- 48.937550R net;
- 0.160979R expectancy;
- 8.632571R maximum drawdown;
- 5.668942 return/DD.

E6 is a research baseline only. It does not replace the control and is not deployable.

## Frozen advanced-test programme

### Block 1 — E6 mechanism

Diagnostic comparison of E6-kept and E6-rejected trades, including MFE, MAE, target/stop path, latency, BOS quality, friction and reward-space geometry. This block cannot select a filter.

### Blocks 2–3 — Selectable candidate families

Path quality:

- P1: sweep-to-entry path no longer than 12 five-minute bars;
- P2: BOS quality score at least two of three;
- P3: entry extension no greater than 0.35R from pivot.

Reward space:

- R1: nearest known structural level is at least 1.25R ahead;
- R2: nearest known structural level is at least 2.50R ahead; shadow unless at least 250 trades.

Only authorized interaction: P2 + R1, shadow-only.

### Block 4 — Portfolio sequencing

- first trade per ETH date;
- 60-minute post-exit cooldown;
- independently risk-normalized session sleeves.

### Blocks 5–6 — Diagnostics

- official FOMC, CPI, NFP, expiration, early-close and rollover attribution;
- 0.50%, 1.00% and 1.50% fixed-fraction equity stress under one-, two- and four-tick-each-side assumptions.

## Historical decision boundary

No historical result can replace E6 or authorize Pine. A rule may only be classified as:

- `FRESH_OOS_CHALLENGER`;
- `SHADOW_ONLY`;
- `REJECT`;
- `DIAGNOSTIC_ONLY`.

At least 250 trades, material effect, return/DD improvement, cost robustness, temporal stability, concentration control and familywise incremental significance are required for fresh-OOS challenger status.

## Previous Monday × Asia decision

Decision: `RETAIN_TUE_FRI_AND_ASIA`.

The advanced-test framework retains Tuesday–Friday and Asia, London and New York. It does not reopen weekday or session selection.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No E6 threshold change, neighboring-threshold search, weekday/session search, additional interaction, Pine port, sizing recommendation, leverage increase or deployment is authorized.
