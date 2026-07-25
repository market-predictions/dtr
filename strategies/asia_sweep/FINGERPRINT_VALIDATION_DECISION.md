# Asian Sweep Fingerprint Study — Untouched Validation Decision

Date: `2026-07-25`  
Validation run: `30178537776`  
Validated head: `f0aadc73871d04c60532af95064868f7a7e960a7`  
Decision artifact: `sha256:d04529762c665751063ec93d6723dd27ab49909e4961d11d60dcd3150415c8ba`

## Decision

`PASS_VALIDATION_FREEZE_AUTHORIZE_2024_2025_FINAL_HOLDOUT`

All twelve preregistered predicates passed on the first untouched application of the frozen model to 2022–2023.

This authorizes a future one-time 2024–2025 final holdout. It does not itself authorize strategy P&L, execution rules, stop/target optimisation, pair or weekday selection, Pine, alerts or deployment.

## Frozen model

The validation used the exact development bundle from Actions run `30177831134` without fitting or recalibration:

- decision point: `T5`, restricted to candidates unresolved five completed minutes after the sweep;
- family: histogram gradient boosting;
- `learning_rate=0.04`;
- `max_leaf_nodes=7`;
- `min_samples_leaf=50`;
- `l2_regularization=5.0`;
- `max_iter=120`;
- frozen pair-week abstention threshold: `0.18252984704127595`.

## Untouched 2022–2023 evidence

| Metric | Validation result | Frozen gate |
|---|---:|---:|
| T5 candidate sweeps | `849` | ≥100 |
| Strict successes | `149` | ≥30 |
| Base success rate | `17.5501%` | descriptive |
| PR-AUC | `0.387839` | ≥25% relative lift |
| PR-AUC relative lift | `+120.99%` | pass |
| ROC-AUC | `0.731812` | descriptive |
| Brier score | `0.129235` | below constant baseline |
| Validation-prevalence Brier baseline | `0.144700` | pass |
| Calibration intercept | `0.419616` | descriptive |
| Calibration slope | `1.247613` | 0.5–1.5 |
| Top-quintile success | `40.0000%` | ≥1.75× base |
| Top-quintile lift | `+127.92%` | pass |
| Bottom-quintile success | `4.7337%` | below base |
| Pair-week Hit@1 | `31.4010%` | ≥25% relative lift |
| Naive pair-week baseline | `16.9427%` | — |
| Hit@1 relative lift | `+85.34%` | pass |

## Breadth

### By pair

| Pair | Candidates | Successes | Base | Top quintile | Relative lift |
|---|---:|---:|---:|---:|---:|
| EURUSD | 427 | 75 | 17.5644% | 43.7500% | +149.08% |
| GBPUSD | 422 | 74 | 17.5355% | 36.6667% | +109.10% |

### By year

| Year | Candidates | Successes | Base | Top quintile | Relative lift |
|---|---:|---:|---:|---:|---:|
| 2022 | 410 | 71 | 17.3171% | 36.5854% | +111.27% |
| 2023 | 439 | 78 | 17.7677% | 43.1818% | +143.04% |

Top-quintile lift was also positive for both upper and lower sweeps and on every weekday. No pair, year, direction or weekday rescue was required.

## Frozen abstention rule

The unchanged development threshold selected candidates in `158 / 207 = 76.33%` of validation pair-weeks.

- selected success rate: `36.0759%`;
- EURUSD selected success: `36.8421%`;
- GBPUSD selected success: `35.3659%`;
- 2022 selected success: `35.3659%`;
- 2023 selected success: `36.8421%`.

This is diagnostic evidence that the development threshold transported without recalibration. It remains secondary to the primary validation gates.

## Stable fingerprint preservation

All five development fingerprints preserved their preregistered observed direction:

| Fingerprint | Expected | Low quartile | High quartile | Validation effect |
|---|---|---:|---:|---:|
| Later sweep minute | Positive | 9.4340% | 17.4528% | +8.0189 pp |
| T5 reclaim depth | Positive | 7.5472% | 31.6038% | +24.0566 pp |
| T5 favorable excursion | Positive | 12.2642% | 30.1887% | +17.9245 pp |
| Asian-range ATR × sweep minute | Negative | 19.8113% | 13.6792% | −6.1321 pp |
| Sweep wick fraction | Positive | 13.6792% | 24.0566% | +10.3774 pp |

The frozen model's partial-dependence direction also agreed for every fingerprint.

## Interpretation

The result validates the core fingerprint hypothesis:

- the raw Asian boundary sweep is not sufficient;
- a sweep still unresolved at five minutes can be ranked materially better using causal context and confirmation data;
- deeper reclaim and favorable movement during T5 carry the strongest observed separation;
- later sweep timing is favorable only conditionally, because proportionally wide Asian ranges increasingly penalize late timing;
- wick structure adds stable information;
- the fingerprint transfers across both pairs and both untouched years.

This is predictive validation of the strict midpoint outcome, not evidence of profitability. Spread, slippage, entry timing, stops, targets and trade management remain untested.

## Independent verification

A separate reconstruction from the raw EURUSD and GBPUSD validation event ledgers and the serialized frozen model reproduced:

- the exact `849`-event T5 population and `149` successes;
- every event ID and target;
- all `849` model probabilities to a maximum absolute difference below `1e-16`;
- year-block quintiles exactly;
- PR-AUC, ROC-AUC, Brier, calibration, top and bottom quintiles exactly;
- all `207` pair-week selections and Hit@1 arithmetic;
- every stable-fingerprint quartile direction and effect.

No discrepancy was found.

## Boundary and next gate

The 2024–2025 holdout remains unopened. Before opening it, a final-holdout contract must be frozen that reuses the exact bundle, feature order, probability threshold, fingerprint directions and evaluation gates without modification.

Only a successful final holdout could authorize the subsequent executable-strategy research stage.
