# DTR Optimization Lab Status

## Current stacked work package

`DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space execution`

Status: **research complete; independent review passed; publication branch active**

Decision state: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`

Base dependency: `DTR-NQ-WP-20260722-10 — E6 advanced test framework` remains a stacked draft on PR #10.

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

### Mechanism audit

Decision: `SUPPORTED`.

Compared with the 182 signals rejected near the prior-day directional extreme, the 296 E6-kept signals with available context had:

- +0.224414R higher expectancy;
- 7.1 percentage points fewer stop-first outcomes;
- higher MFE;
- higher TP1 and TP2 hit rates;
- higher expectancy in all three tested years and all three sessions.

The mechanism is consistent with increased continuation or failed-reversal risk near the prior-day directional extreme. The 0.25 ATR threshold remains frozen.

### Candidate result

- P1 path ≤12 bars: 93 trades; `REJECT`.
- P2 BOS quality 2/3: 225 trades; `SHADOW_ONLY`.
- P3 entry extension ≤0.35R: 208 trades; `SHADOW_ONLY`.
- R1 clear to TP1: 99 trades; `REJECT`.
- R2 clear to runner: 46 trades; predeclared `SHADOW_ONLY` diagnostic.
- I1 P2 + R1: 76 trades; predeclared `SHADOW_ONLY` interaction.

Every candidate produced less total return than E6 after complete portfolio resequencing. All paired confidence intervals crossed zero and all selectable familywise incremental p-values were 1.0. No candidate qualified as `FRESH_OOS_CHALLENGER`.

### Verification

- archive checksum matched;
- 477-trade control and 304-trade E6 regressions exact;
- all metrics, costs, masks and changed trades independently reconstructed;
- D1 and weekly context timestamps causal;
- sweep ≤ reclaim ≤ BOS ≤ entry ordering verified;
- no overlapping positions;
- independent bootstrap agreed;
- 17 runner artifacts identical across two complete executions.

## Next authorized work

Block 4 portfolio sequencing:

- S0: current global one-position sequencing;
- S1: first eligible E6 trade per ETH market date;
- S2: 60-minute cooldown after exit;
- S3: independent Asia, London and New York sleeves with one-third risk per sleeve.

Blocks 0–3 may not be retuned or combined further on the 2023–2025 sample.

## Existing unresolved gates

- authoritative timestamp metadata or qualified replacement dataset: `UNRESOLVED`;
- continuous-contract methodology: `UNRESOLVED`;
- original 904-search familywise adjustment: `UNRESOLVED_EXACT_RECONSTRUCTION_BLOCKED`;
- qualified fresh OOS Arms 0/A/B: `NOT_RUN_PREREGISTERED`;
- Python/Pine parity: `NOT_RUN`.

## Scope restrictions

No E6 threshold change, neighboring-threshold search, weekday/session search, additional interaction, Pine port, sizing recommendation, leverage increase or deployment is authorized.
