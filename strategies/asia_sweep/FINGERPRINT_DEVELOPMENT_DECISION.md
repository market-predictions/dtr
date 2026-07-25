# Asian Sweep Fingerprint Study — Development Model Decision

Date: `2026-07-25`  
Decision run: `30177831134`  
Accepted head: `314447539d6093fa846dca485369cebd053fd8b5`  
Decision artifact: `sha256:6f6399d65ee0fc5e0a7018d412cd75d85a90d324e6624f988c3fbd565008521a`

## Decision

`PASS_DEVELOPMENT_FREEZE_AUTHORIZE_2022_2023_VALIDATION`

This decision authorizes one untouched application of the frozen fingerprint model to 2022–2023. It does not authorize 2024–2025, strategy P&L, entry/stop/target optimization, pair or weekday selection, Pine, alerts or deployment.

## Selected model

- decision landmark: `T5`, restricted to events unresolved five completed minutes after the sweep;
- family: histogram gradient boosting;
- frozen parameters:
  - `learning_rate=0.04`;
  - `max_leaf_nodes=7`;
  - `min_samples_leaf=50`;
  - `l2_regularization=5.0`;
  - `max_iter=120`;
- development population: `2,900` events;
- strict 09:00–10:00 midpoint successes: `474`;
- base success rate: `16.3448%`.

## Grouped out-of-fold performance

Seven leave-one-year-out folds covered each development event exactly once.

| Metric | Selected T5 model | Frozen development requirement |
|---|---:|---:|
| PR-AUC | `0.311725` | relative lift ≥15% |
| PR-AUC relative lift | `+90.72%` | pass |
| ROC-AUC | `0.695504` | descriptive |
| Brier score | `0.126942` | below baseline |
| Fold-prevalence Brier baseline | `0.136876` | pass |
| Calibration intercept | `-0.05594` | descriptive |
| Calibration slope | `0.95501` | 0.4–1.8 |
| Top-quintile success | `32.6460%` | ≥1.50× base |
| Top-quintile lift | `+99.73%` | pass |
| Bottom-quintile success | `5.7093%` | below base |
| Pair-week Hit@1 | `25.8550%` | ≥15% relative lift |
| Naive weekly baseline | `15.5959%` | — |
| Hit@1 relative lift | `+65.78%` | pass |

Top-quintile lift was positive on both pairs, both sweep directions, every weekday and all seven development years.

Pair results:

- EURUSD: base `15.8076%`, top quintile `33.1034%`;
- GBPUSD: base `16.8858%`, top quintile `32.1918%`.

## Frozen abstention rule

The lowest development threshold satisfying the preregistered abstention requirements was:

- OOF prediction quantile: `0.70`;
- probability threshold: `0.18252984704127595`;
- candidate pair-week coverage: `545 / 731 = 74.56%`;
- selected-event success rate: `29.9083%`;
- relative lift over the T5 development base: `+82.98%`;
- positive on both pairs and all seven years.

The threshold is frozen and cannot be recalculated on validation data.

## Five frozen stable fingerprints

The selected nonlinear model produced these five highest-ranked directional fingerprints, each directionally consistent in all seven outer folds:

1. later `sweep_minute`: positive;
2. deeper `t5_reclaim_depth_range_fraction`: positive;
3. greater `t5_mfe_range_fraction`: positive;
4. `asian_range_atr20 × sweep_minute`: negative;
5. greater `sweep_wick_range_fraction`: positive.

The fourth interaction qualifies the first fingerprint: later sweeps were more favorable when the Asian range was not proportionally wide; a wide range increasingly penalized later sweep timing.

## Rejected candidates

Both elastic-net logistic candidates failed the Brier and calibration gates and did not achieve the required top-quintile lift. The T0 nonlinear candidate passed all development predicates but ranked behind the T5 nonlinear model under the frozen hierarchy:

- T0 nonlinear PR-AUC: `0.251763`;
- T0 nonlinear top-quintile success: `25.6011%`;
- T0 nonlinear Hit@1: `23.9071%`.

This supports the prior anatomy finding that the first five minutes add meaningful information beyond context at the sweep.

## Independent verification

A separate reconstruction from the raw event ledgers reproduced:

- T5 landmark population `2,900` and success count `474`;
- all `2,900` unique OOF predictions across 2015–2021;
- PR-AUC, ROC-AUC, Brier scores and quintile rates exactly;
- all `731` pair-week selections and Hit@1 arithmetic;
- calibration intercept and slope;
- both-pair and all-year lift predicates;
- the frozen `0.70` abstention-quantile rule.

No discrepancy was found.

## Boundary

The model remains diagnostic and predictive. Only the frozen 2022–2023 validation may now be opened. Failure of any validation predicate stops this formulation before 2024–2025 and before executable strategy research.
