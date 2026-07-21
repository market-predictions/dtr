# DTR Optimization Lab Status

## Current work package

`DTR-NQ-WP-20260721-04 — CISD entry-confirmation ablation`

Status: **complete; final CI passed; ready for PR merge**

Branch: `agent/nq-cisd-ablation`

PR: `#4 — Reject CISD confirmation after causal NQ ablation`

Decision: `REJECT_NO_INCREMENTAL_VALUE`

## Locked primary dataset

Dataset SHA-256:

`8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`

NQ remains the sole optimization base for the current phase.

## Frozen reversal baseline

`DTR_PY_NQ_CANDIDATE_0_1_GAP_SAFE`

- trades: `491`;
- expectancy: `0.180235811449135R`;
- net R: `88.49578342152539R`;
- profit factor: `1.3819983049452256`;
- maximum drawdown: `14.107857513807524R`;
- return-to-drawdown: `6.272801`.

The baseline remains unchanged.

## Closed module decisions

- continuation: `HOLD_FOR_FRESH_DATA`;
- IFVG confirmation: `REJECT_NO_INCREMENTAL_VALUE`;
- CISD confirmation: `REJECT_NO_INCREMENTAL_VALUE`.

None may be retuned or combined on the current NQ sample.

## CISD result

Broad CISD confirmation is inferior to the frozen baseline:

- sequence confirm: 309 trades, 0.144100R expectancy, 4.464679 return/DD;
- last-candle confirm: identical to sequence confirm;
- recent ≤3 bars: 296 trades, 0.136305R expectancy;
- recent ≤6 bars: 309 trades, 0.140105R expectancy.

The retest portfolio has 75 trades and 0.256552R expectancy, but only 15.3% coverage and 3.728646 return/DD. Its frozen 73-trade cohort has a 0.130746R point-estimate uplift over the complement, but trade and month-block confidence intervals cross zero and the one-sided permutation p-value is 0.210289.

CISD retest is retained as a diagnostic annotation only. It is not authorized as a filter or sizing rule.

## Validation status

- causal bullish/bearish implementation: **complete**;
- final-candle anchor fixtures: **passed**;
- stale confirmed/unconfirmed sequence expiry: **passed**;
- reset-epoch fixtures: **passed**;
- strict manifest tests: **passed**;
- full suite: **62 tests passed**;
- frozen observe regression: **passed**;
- exact changed-trade attribution: **complete**;
- deterministic clean repeat: **52/52 artifacts byte-identical**;
- cost stress: **complete**;
- bootstrap and permutation analysis: **complete**;
- independent adversarial review: **complete**;
- pinned Ruff: **passed**;
- pytest Python 3.11: **passed**;
- pytest Python 3.12: **passed**;
- GitHub CI run `29875052056`: **success**.

## Promotion restriction

CISD may not be added to the reversal candidate, used for position sizing, combined with IFVG or continuation, tuned further on the current sample, or ported to Pine as a strategy rule.

## Next planned work package

`DTR-NQ-WP-20260722-05 — Reversal entry-routing ablation`

It will compare the frozen break-close route with a causally defined first-pullback route and a predeclared hybrid router while preserving signal, stop, target, and exit logic.

## Open project limitations

- continuous-contract rollover and back-adjustment methodology;
- exact timestamp and daylight-saving semantics;
- session-boundary and supplied VWAP reset verification;
- absence of post-December-2025 paper-forward data.
