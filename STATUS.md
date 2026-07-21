# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-03 — IFVG entry-confirmation ablation`

Status: **complete; awaiting final CI and PR merge**

Branch: `agent/nq-ifvg-ablation`

PR: `#3 — Test IFVG confirmation on frozen NQ reversal`

Decision: `REJECT_NO_INCREMENTAL_VALUE`

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole optimization base for the current phase. Other instruments and feeds are deferred.

## Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- trades: `491`
- net R: `88.49578342152539`
- expectancy: `0.180235811449135R`
- profit factor: `1.3819983049452256`
- maximum drawdown: `14.107857513807524R`

The baseline remains unchanged.

## Held continuation result

`CONT_A2_PULLBACK_LATE60` remains `HOLD_FOR_FRESH_DATA`. It may not be retuned or combined with reversal on the current sample.

## IFVG result

All five predeclared implementable IFVG filters lower aggregate expectancy versus the frozen reversal baseline.

- any aligned IFVG: 455 trades, 0.168419R expectancy;
- recent ≤3 bars: 318 trades, 0.168385R;
- recent ≤6 bars: 367 trades, 0.157503R;
- recent ≤12 bars: 432 trades, 0.160347R;
- post-inversion zone touch: 212 trades, 0.153369R.

Any aligned IFVG covers 92.7% of baseline trades and is weakly selective. Stricter filters lose substantial opportunity and enable a small number of later trades that are net negative. One-, two-, and four-tick cost stress preserves the rejection.

## Validation status

- causal bullish/bearish IFVG implementation: **complete**;
- no-lookahead and reset-epoch fixtures: **passed**;
- frozen observe regression: **passed**;
- exact changed-trade attribution: **complete**;
- deterministic clean repeat: **52/52 artifacts byte-identical**;
- pinned Ruff: **passed**;
- pytest Python 3.11: **passed**;
- pytest Python 3.12: **passed**;
- GitHub CI implementation run `29860594349`: **success**;
- independent adversarial review: **complete**.

## Promotion restriction

IFVG may not be added to the reversal candidate, combined with continuation, tuned further on the current NQ sample, or ported to Pine as a strategy rule.

## Next planned work package

`DTR-NQ-WP-20260721-04 — CISD entry-confirmation ablation`

CISD will be defined causally and tested independently against the frozen 491-trade gap-safe reversal baseline. It must separate cohort association from implementable portfolio effects and stop when incremental value is absent.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
