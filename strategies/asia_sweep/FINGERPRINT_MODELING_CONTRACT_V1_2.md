# Asian Sweep Fingerprint Study — Modelling Contract v1.2

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Parent contracts:

- `FINGERPRINT_STUDY_PREREGISTRATION.md` v1.1.0;
- `FINGERPRINT_STUDY_FEATURE_AMENDMENT_V1_1.md`.

Status: `FROZEN_BEFORE_GROUPED_MODEL_OUTPUT_INSPECTION`

This contract freezes the exact development modelling, landmarking, cross-validation, model-selection, weekly-ranking, abstention and validation-authorisation rules. It is binding before any grouped out-of-fold PR-AUC, Brier score, calibration, coefficient, feature importance, Hit@1 result or 2022–2023 outcome is inspected.

## 1. Scientific objective

The objective is to determine whether information available at either:

- `T0`: the close of the first qualifying sweep minute; or
- `T5`: five completed minutes after that sweep,

can rank and calibrate the probability of the frozen primary outcome:

`MIDPOINT_SUCCESS_09_10`

The programme is not authorised to calculate executable strategy P&L, optimise entries, stops or targets, remove weekdays, select only one pair or direction, narrow the clock window, or inspect 2022–2025 outcomes during development.

## 2. Development evidence

The only modelling input is the immutable 2015–2021 EURUSD and GBPUSD anatomy evidence produced by GitHub Actions run `30174245825` at commit `8b1946a40fd9b01069f8c6084fe425bda6d830d2`.

Expected immutable artifact digests:

- EURUSD: `sha256:90d70d152f895c7a6eece0e167832047896607605392bb1bc890869a524b68a3`;
- GBPUSD: `sha256:391b649f550008f1f6ae1e87509b47523997c5140fe2d4bafaf81e76cbca48fd`;
- pooled anatomy report: `sha256:c5579d3a712b7b886f8dad1025187083e8b58a8851a6c0def286923894862d0e`.

The modelling workflow must reject any input outside 2015–2021 or any missing pair.

## 3. Frozen populations

### 3.1 T0 population

The T0 population contains every frozen primitive sweep candidate in the 2015–2021 ledgers, including all frozen outcome classes. The binary target is:

- `1`: `midpoint_success_09_10 == true`;
- `0`: every other frozen primary outcome.

No event is removed because it later becomes an early reversal, late reversal, false reversal, continuation, stalled reaction or two-sided ambiguity.

### 3.2 T5 landmark population

The T5 model answers a conditional question: among candidates still unresolved five completed minutes after the sweep, which subsequently become a strict 09:00–10:00 midpoint success?

An event enters the T5 landmark population only when:

- `t5_available == true`;
- no midpoint first passage has occurred at or before `t5_timestamp_utc`;
- no continuation-barrier first passage has occurred at or before `t5_timestamp_utc`;
- no opposite-boundary first passage has occurred at or before `t5_timestamp_utc`.

A reaction-only first passage does not resolve the event and therefore does not exclude it. Early midpoint, late midpoint and other outcomes remain negative labels when they are unresolved at T5.

This landmarking rule prevents the five-minute features from predicting an outcome that already occurred during those same five minutes.

## 4. Cross-pair causal features

EURUSD and GBPUSD events from the same Amsterdam date may inform one another only when the other-pair information was already observable at the current decision timestamp.

### 4.1 T0 cross-pair features

For each event, use the most recent opposite-pair sweep whose sweep timestamp is at or before the current T0:

- other-pair sweep observed flag;
- minutes since that sweep;
- same-side versus opposite-side sweep flag;
- other-pair sweep depth in Asian-range fractions.

Also record:

- same-side opposite-pair sweep within five clock minutes;
- opposite-side opposite-pair sweep within fifteen clock minutes.

The latter proximity features may use the current timestamp only; no future opposite-pair sweep is permitted. A sweep occurring after the current decision timestamp cannot be used.

### 4.2 T5 cross-pair features

At T5, the latest opposite-pair T5 snapshot may be used only when its `t5_timestamp_utc` is at or before the current event's T5 timestamp. Frozen fields:

- other-pair T5 snapshot known flag;
- other-pair reclaim flag;
- other-pair five-minute reversal-signed return;
- other-pair retest-hold flag;
- other-pair reversal-swing-break flag.

Missing opposite-pair information remains missing and is handled inside the training fold.

## 5. Frozen feature matrices

Raw price levels, event IDs, trade dates, outcome timestamps, future-path metrics and outcome labels are prohibited as model inputs.

### 5.1 T0 categorical features

- `instrument`;
- `side`;
- `weekday`;
- `week_of_month`;
- `sweep_half_hour`;
- `asian_compression_bucket`;
- `sweep_consumption_class`.

### 5.2 T0 binary and numeric features

Time and range:

- `sweep_minute`;
- `sweep_before_0900`;
- `asian_range_pips`;
- `asian_range_atr20`;
- `asian_range_adr20`;
- `asian_range_vs_median20`;
- `asian_range_percentile20`;
- `asian_range_percentile60`;
- `asian_range_zscore60`;
- `asian_range_under_20_pip_flag`;
- `asian_range_20_30_pip_flag`;
- `asian_range_over_30_pip_flag`.

Asian-session structure:

- `asian_close_location`;
- `asian_return_range_fraction`;
- `asian_realized_vol_range_fraction`;
- `asian_high_formation_minute`;
- `asian_low_formation_minute`;
- `asian_high_zone_touches`;
- `asian_low_zone_touches`;
- `asian_direction_changes`;
- `asian_first_half_range_fraction`;
- `asian_second_half_range_fraction`.

Pre-sweep path:

- `pre_sweep_return_range_fraction`;
- `pre_sweep_reversal_signed_return`;
- `pre_sweep_realized_vol_range_fraction`;
- `pre_sweep_boundary_tests`;
- `pre_sweep_minutes_from_0800`;
- `pre_sweep_trailing_15m_range_fraction`.

Sweep mechanics:

- `sweep_depth_pips`;
- `sweep_depth_range_fraction`;
- `sweep_body_range_fraction`;
- `sweep_wick_range_fraction`;
- `sweep_close_beyond_boundary_fraction`;
- `sweep_close_location_in_bar`;
- `sweep_displacement_vs_trailing_vol`.

Completed higher-timeframe context:

- `prior_day_return_atr20`.

T0 same-side liquidity topology:

- `same_side_level_count`;
- `same_side_source_diversity`;
- `nearest_same_side_distance_atr`;
- `second_same_side_distance_atr`;
- `third_same_side_distance_atr`;
- `same_side_levels_within_0_05_atr`;
- `same_side_levels_within_0_10_atr`;
- `same_side_levels_within_0_20_atr`;
- `same_side_levels_within_0_25_range`;
- `same_side_source_families_within_0_10_atr`;
- `same_side_weighted_density`;
- `stack_present`;
- `stack_member_count`;
- `stack_source_diversity`;
- `stack_centroid_distance_atr`;
- `stack_span_atr`;
- `stack_contains_equal_cluster`;
- `levels_consumed_before_sweep`;
- `levels_consumed_by_sweep`;
- `stack_fraction_consumed_t0`;
- `full_stack_exhausted_t0`;
- `remaining_levels_beyond_t0`;
- `nearest_remaining_distance_atr_t0`;
- `residual_density_t0`;
- `sweep_stops_inside_stack`.

Opposing destination:

- `opposite_level_count`;
- `opposite_source_diversity`;
- `nearest_opposite_distance_atr`;
- `midpoint_before_nearest_opposite`.

Frozen T0 cross-pair features from section 4.1 are appended.

### 5.3 T5 incremental features

The T5 matrix contains every T0 feature plus:

- `t5_closes_outside`;
- `t5_closes_inside`;
- `t5_reclaim`;
- `t5_reclaim_delay_minutes`;
- `t5_reclaim_depth_range_fraction`;
- `t5_return_range_fraction`;
- `t5_mfe_range_fraction`;
- `t5_mae_range_fraction`;
- `t5_extreme_extension_range_fraction`;
- `t5_retest_touch`;
- `t5_retest_hold`;
- `t5_reversal_swing_break`;
- `levels_consumed_through_t5`;
- `stack_fraction_consumed_t5`;
- `full_stack_exhausted_t5`;
- `remaining_levels_beyond_t5`;
- `nearest_remaining_distance_atr_t5`;
- `residual_density_t5`;
- frozen T5 cross-pair fields from section 4.2.

### 5.4 Frozen explicit interactions for the elastic-net model

The following products are computed inside each model pipeline after fold-local imputation/scaling of their primitive numeric inputs:

- range ATR normalization × sweep depth;
- range ATR normalization × sweep minute;
- range ATR normalization × pre-sweep realised volatility;
- range ATR normalization × same-side weighted liquidity density;
- range ATR normalization × residual liquidity density;
- range ATR normalization × T5 reclaim depth for T5 only.

No other manual interaction is introduced after development scores are seen.

## 6. Preprocessing

All preprocessing is fitted on the training fold only.

Numeric features:

- replace positive or negative infinity with missing;
- median imputation;
- append missingness indicators for columns with training-fold missing values;
- robust scaling using training-fold median and interquartile range.

Categorical features:

- most-frequent imputation;
- one-hot encoding with unknown categories ignored.

No target encoding, global imputation, global scaling or pre-CV feature deletion is permitted.

Features that are constant within a training fold may be removed inside that fold. Correlated features remain available to elastic-net shrinkage; no outcome-guided manual pruning is permitted.

## 7. Grouped nested cross-validation

### 7.1 Outer folds

Use seven chronological leave-one-year-out outer folds:

- each of 2015, 2016, 2017, 2018, 2019, 2020 and 2021 is the test block once;
- the remaining six development years are training data;
- EURUSD and GBPUSD observations from the same Amsterdam date therefore remain together;
- no random event-level split is permitted.

The complete out-of-fold prediction ledger must contain exactly one prediction per eligible event.

### 7.2 Inner folds

Within each outer-training partition, use leave-one-training-year-out inner folds. Hyperparameters are selected by:

1. highest pooled inner-fold average precision (`PR-AUC`);
2. lower pooled Brier score when PR-AUC differs by less than `0.002`;
3. stronger regularisation when both metrics remain tied;
4. lexicographic parameter order as the final deterministic tie-break.

No outer-test result may influence hyperparameter selection.

## 8. Frozen model families and grids

All random seeds are `20260725`.

### 8.1 Primary interpretable family

Scikit-learn elastic-net logistic regression with:

- solver: `saga`;
- penalty: `elasticnet`;
- no class weighting;
- maximum iterations: `5000`;
- tolerance: `1e-4`.

Grid:

- `C`: `[0.02, 0.05, 0.1, 0.2, 0.5, 1.0, 2.0]`;
- `l1_ratio`: `[0.0, 0.25, 0.5, 0.75, 1.0]`.

### 8.2 Nonlinear challenger

Scikit-learn histogram gradient boosting classifier with:

- loss: `log_loss`;
- early stopping disabled;
- maximum iterations: `250`.

Grid:

- `learning_rate`: `[0.03, 0.06]`;
- `max_leaf_nodes`: `[7, 15, 31]`;
- `min_samples_leaf`: `[20, 50]`;
- `l2_regularization`: `[1.0, 5.0]`.

Categorical variables are one-hot encoded for both model families to preserve an identical audited feature contract.

## 9. Metrics

Metrics are computed from pooled outer-fold predictions and also separately by pair, year, side and weekday.

Required event metrics:

- base success rate;
- average precision (`PR-AUC`);
- ROC-AUC;
- Brier score;
- constant-probability Brier baseline using the outer-training prevalence for each test fold;
- calibration intercept and slope from an unpenalised logistic recalibration of outcome on prediction log-odds;
- top-quintile success rate and relative lift;
- bottom-quintile success rate;
- decile calibration table.

Quintiles are assigned within each outer-test fold using the training-fold prediction distribution where available; deterministic rank-percentile fallback is permitted for tied discrete challenger predictions.

## 10. Pair-week ranking

For each `instrument × Amsterdam week_key` group:

- rank eligible candidates by out-of-fold predicted probability;
- deterministic ties resolve by earlier sweep timestamp, then event ID;
- `Hit@1` is one when the selected top candidate succeeds;
- naive baseline is the average within-week random-choice success probability: successes in week divided by candidates in week;
- regret is one when the week contains a success but the top-ranked candidate fails.

Report:

- Hit@1 and relative lift over the naive baseline;
- successful-week Hit@1;
- regret;
- number of candidates per week;
- separate pair and year results.

## 11. Abstention rule

An abstaining weekly selector is frozen using development out-of-fold predictions only.

Candidate probability thresholds are the pooled development prediction quantiles:

`[0.50, 0.60, 0.70, 0.80, 0.90]`.

Choose the lowest quantile threshold that simultaneously provides:

- opportunity coverage of at least `25%` of candidate pair-weeks;
- selected-event success rate at least `1.75 ×` the relevant development base rate;
- positive selected-event lift on both pairs;
- positive selected-event lift in at least five of seven years.

If no threshold qualifies, freeze `NO_ABSTENTION_THRESHOLD` and do not create one after validation is opened.

## 12. Deterministic final-model selection

Four candidates are evaluated:

- T0 elastic net;
- T0 histogram gradient boosting;
- T5 elastic net;
- T5 histogram gradient boosting.

A candidate is development-eligible only when all of the following pass:

1. pooled PR-AUC relative lift over base rate is at least `15%`;
2. top-quintile success is at least `1.50 ×` base rate;
3. bottom-quintile success is below base rate;
4. Brier score improves on the fold-specific constant baseline;
5. Hit@1 relative lift over the naive baseline is at least `15%`;
6. both pairs show positive top-quintile lift;
7. at least five of seven years show positive top-quintile lift;
8. calibration slope is between `0.4` and `1.8`.

Selection hierarchy among eligible models:

1. highest pooled PR-AUC;
2. if PR-AUC differs by less than `0.01`, prefer lower Brier score;
3. if still tied, prefer elastic net over the nonlinear challenger;
4. if still tied, prefer T0 over T5 because it is earlier and less execution-delayed.

If no candidate is eligible, the programme does not open 2022–2023 under this formulation.

## 13. Stable fingerprints

For the selected final model, identify the five highest-ranked stable fingerprints.

Elastic net:

- rank by median absolute standardised coefficient across outer folds;
- require the same non-zero coefficient sign in at least five of seven folds.

Histogram gradient boosting:

- use training-fold permutation importance evaluated on the corresponding outer test fold;
- require positive importance in at least five of seven folds;
- direction is determined by a frozen one-feature partial-dependence contrast between the 25th and 75th training-fold percentiles and must agree in at least five folds.

One-hot levels are mapped back to their parent feature for validation-direction testing. No fingerprint is substituted after validation results are seen.

## 14. Validation authorisation

The 2022–2023 source partition remains closed until a compact development decision artifact records:

- all model metrics;
- full out-of-fold prediction ledger;
- selected or rejected final model;
- exact hyperparameter selections by outer fold;
- frozen feature order;
- frozen preprocessing contract;
- frozen stable fingerprint list and expected directions;
- frozen abstention threshold or explicit absence of one;
- every development-eligibility predicate.

Only `PASS_DEVELOPMENT_FREEZE_AUTHORIZE_2022_2023_VALIDATION` permits the next workflow. Otherwise the programme stops this fingerprint formulation before validation and before strategy P&L.

## 15. Required falsification tests

Before development model output is accepted, automated tests must prove:

- T5 landmark exclusion of already resolved events;
- no outcome or forward-path columns enter either matrix;
- cross-pair features cannot use a timestamp later than the current decision point;
- outer folds are complete, mutually exclusive and year-blocked;
- preprocessing is fitted inside folds;
- each eligible event receives exactly one OOF prediction;
- shuffled labels remove predictive lift within tolerance;
- event-order permutation does not change results;
- appending future years does not change earlier feature rows or fold assignments;
- pair-week tie resolution is deterministic;
- validation and holdout files are rejected by the development workflow.
