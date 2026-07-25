# Asian Sweep Fingerprint Study — Final Holdout Decision

Date: `2026-07-26`  
Final holdout run: `30179786981`  
Evaluated head: `7bbb2ab78577f67e96da90199d515347211e1e35`  
Decision artifact: `sha256:885650868fed6009907649f735a92ef106d5eea85f58233be6d080c1fe67c112`

## Decision

`PASS_FINAL_HOLDOUT_AUTHORIZE_EXECUTABLE_STRATEGY_RESEARCH`

All twelve frozen predicates passed on the first and only untouched application of the frozen T5 model to EURUSD and GBPUSD in 2024–2025.

This validates the predictive fingerprint programme through development, untouched validation and final untouched holdout. It does not establish profitability and does not authorize deployment.

## Frozen model and provenance

The final holdout used the unchanged serialized development bundle:

- development anatomy run: `30174245825`;
- frozen development model run: `30177831134`;
- untouched validation run: `30178537776`;
- decision point: T5, restricted to candidates unresolved five completed minutes after the sweep;
- family: histogram gradient boosting;
- `learning_rate=0.04`;
- `max_leaf_nodes=7`;
- `min_samples_leaf=50`;
- `l2_regularization=5.0`;
- `max_iter=120`;
- frozen pair-week abstention threshold: `0.18252984704127595`;
- scikit-learn: `1.9.0`.

No fitting, recalibration, threshold adjustment, pair/day/direction selection or feature substitution occurred.

## Untouched 2024–2025 results

| Metric | Final holdout result | Frozen gate |
|---|---:|---:|
| T5 candidate sweeps | `769` | ≥100 |
| Strict midpoint successes | `140` | ≥30 |
| Base success rate | `18.2055%` | descriptive |
| PR-AUC | `0.333150` | ≥25% relative lift |
| PR-AUC relative lift | `+82.99%` | pass |
| ROC-AUC | `0.683409` | descriptive |
| Brier score | `0.139846` | below constant baseline |
| Holdout-prevalence Brier baseline | `0.148911` | pass |
| Calibration intercept | `0.246719` | descriptive |
| Calibration slope | `0.989292` | 0.5–1.5 |
| Top-quintile success | `32.9032%` | ≥1.75× base |
| Top-quintile lift | `+80.73%` | pass |
| Bottom-quintile success | `7.8431%` | below base |
| Pair-week Hit@1 | `28.0952%` | ≥25% relative lift |
| Naive pair-week baseline | `18.4649%` | — |
| Hit@1 relative lift | `+52.16%` | pass |

## Breadth

### By pair

| Pair | Candidates | Successes | Base | Top quintile | Relative lift |
|---|---:|---:|---:|---:|---:|
| EURUSD | `381` | `75` | `19.6850%` | `41.3333%` | `+109.97%` |
| GBPUSD | `388` | `65` | `16.7526%` | `25.0000%` | `+49.23%` |

### By year

| Year | Candidates | Successes | Base | Top quintile | Relative lift |
|---|---:|---:|---:|---:|---:|
| 2024 | `391` | `71` | `18.1586%` | `32.9114%` | `+81.24%` |
| 2025 | `378` | `69` | `18.2540%` | `32.8947%` | `+80.21%` |

Both pairs and both years preserved positive top-quintile lift without rescue or refitting.

## Pair-week ranking and frozen abstention

Across `210` pair-weeks:

- highest-ranked-candidate Hit@1: `28.0952%`;
- naive random-candidate baseline: `18.4649%`;
- relative lift: `+52.16%`.

The unchanged development threshold selected `136 / 210 = 64.76%` of pair-weeks:

- selected success rate: `32.3529%`;
- EURUSD: `27 / 67 = 40.30%`;
- GBPUSD: `17 / 69 = 24.64%`;
- 2024: `21 / 68 = 30.88%`;
- 2025: `23 / 68 = 33.82%`.

This remains an outcome-selection result, not an executable trade win rate.

## Stable fingerprint preservation

All five frozen fingerprints preserved their expected observed direction:

| Fingerprint | Expected | Low quartile | High quartile | Effect |
|---|---|---:|---:|---:|
| Later sweep minute | Positive | `15.1042%` | `18.2292%` | `+3.1250 pp` |
| T5 reclaim depth | Positive | `10.4167%` | `28.1250%` | `+17.7083 pp` |
| T5 favorable excursion | Positive | `12.5000%` | `26.5625%` | `+14.0625 pp` |
| Asian-range ATR × sweep minute | Negative | `21.8750%` | `13.0208%` | `−8.8542 pp` |
| Sweep wick fraction | Positive | `14.5833%` | `17.7083%` | `+3.1250 pp` |

The frozen model partial-dependence direction also agreed for every fingerprint.

## Interpretation

The most stable practical conclusion remains:

- the boundary sweep itself is not sufficient;
- the first five completed minutes contain the strongest information;
- a deeper reclaim and meaningful reversal-side favorable excursion are the dominant fingerprints;
- later sweep timing is useful only conditionally, because a proportionally wide Asian range penalizes late sweeps;
- wick structure contributes additional stable information;
- the fingerprint transferred through both untouched stages, both pairs and all four untouched years.

## Independent verification

A separate reconstruction from the raw EURUSD and GBPUSD holdout ledgers and the serialized development model reproduced:

- exactly `769` T5 candidates and `140` successes;
- all event IDs and targets;
- all `769` probabilities with maximum absolute difference `9.72e-17`;
- year-block quintiles;
- PR-AUC, ROC-AUC, Brier and calibration;
- all `210` pair-week rankings and selected event IDs;
- pair/year tables and abstention arithmetic;
- all five observed and model fingerprint directions.

No discrepancy was found.

## Post-holdout continuation observation

The separate continuation/fake-rejection construct remains valid, but the holdout confirms why it must have its own target.

In the bottom reversal-score quintile:

- immediate continuation: `43.79%`;
- false reversal: `16.99%`;
- combined continuation-like classes: `60.78%`;
- strict midpoint reversal: `7.84%`;
- the remaining `31.37%` consisted of stalled, early or late reversal paths.

In the top reversal-score quintile, continuation-like classes still represented `50.97%`, largely because false reversals remained common (`32.26%`).

Therefore:

- low reversal quality increases the incidence of same-side follow-through;
- but `1 - P(reversal)` is not a calibrated continuation probability;
- a continuation classifier must explicitly distinguish immediate continuation and false reversal from stalled, early, late and ambiguous outcomes;
- the eventual decision system should be reversal / continuation / abstain, not a forced binary inversion.

The continuation programme is recorded in `FINGERPRINT_CONTINUATION_TRIAGE_ROADMAP.md` and must use new independent evidence because 2024–2025 is no longer untouched for that hypothesis.

## Authorised next stage

The programme may now open a separate executable-strategy research stage that freezes before P&L inspection:

- actionable entry timestamp after T5;
- bid/ask execution and spread/slippage assumptions;
- stop definition;
- target and time-exit definitions;
- trade overlap and daily exposure rules;
- risk normalization;
- strategy-level discovery, validation and holdout partitions.

Pine, alerts, paper trading and deployment remain blocked until executable P&L survives its own frozen gates.
