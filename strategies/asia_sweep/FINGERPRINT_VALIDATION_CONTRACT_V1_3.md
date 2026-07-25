# Asian Sweep Fingerprint Study — Untouched Validation Contract v1.3

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Status: `FROZEN_BEFORE_2022_2023_OUTCOME_INSPECTION`

Applies to the development decision recorded in `FINGERPRINT_DEVELOPMENT_DECISION.md` and the frozen bundle produced by GitHub Actions run `30177831134`.

This contract defines the one permitted evaluation of the selected T5 histogram-gradient-boosting model on untouched 2022–2023 data. No 2022–2023 event count, outcome, prediction, feature contrast or gate result was inspected before this contract was committed.

## 1. Immutable inputs

### Frozen model

The validation workflow must download the complete development decision artifact from run `30177831134` and load its exact `frozen_validation_model.joblib`.

Required model provenance:

- development anatomy run: `30174245825`;
- development modelling run: `30177831134`;
- development modelling head: `314447539d6093fa846dca485369cebd053fd8b5`;
- selected landmark: `T5`;
- selected family: `hgb`;
- parameters:
  - `learning_rate=0.04`;
  - `max_leaf_nodes=7`;
  - `min_samples_leaf=50`;
  - `l2_regularization=5.0`;
- frozen abstention probability: `0.18252984704127595`.

No model, preprocessor, feature, threshold or fingerprint may be refitted or recalculated.

### Market data

Only qualified EURUSD and GBPUSD BID/ASK M1 files for calendar years 2022 and 2023 may be used. The same synchronized midpoint, Amsterdam-native session, primitive sweep, label and liquidity-feature engines used for development are authoritative.

The validation workflow must reject:

- any event outside 2022–2023;
- a missing pair or missing year;
- duplicate event IDs;
- any feature-order mismatch;
- any attempt to load 2024–2026 data.

## 2. Validation population

Construct the frozen T5 landmark population exactly as in development:

- `t5_available == true`;
- no midpoint first passage at or before T5;
- no continuation-barrier first passage at or before T5;
- no opposite-boundary first passage at or before T5.

The binary target remains strict `MIDPOINT_SUCCESS_09_10`. All other outcomes are negative labels.

Cross-pair features are reconstructed jointly from EURUSD and GBPUSD and may use only opposite-pair information timestamped at or before the current event's T0 or T5 decision timestamp.

## 3. Frozen predictions

Use the development-fitted preprocessor and classifier without any update:

1. enforce the exact ordered numeric, categorical and interaction manifests stored in the bundle;
2. transform validation rows with development medians, missing indicators, robust centers/scales and one-hot categories;
3. ignore unknown categories only through the frozen encoder behavior;
4. generate one probability per eligible event;
5. prohibit calibration or probability rescaling on validation data.

## 4. Validation quintiles

Assign prediction quintiles separately within each untouched calendar year:

- sort by prediction ascending, then event ID;
- use deterministic rank percentiles;
- quintile 5 is the highest 20% within that year;
- quintile 1 is the lowest 20% within that year.

This mirrors the development outer-year evaluation and prevents one year's prediction distribution from dominating the other.

Pair and year lift tables use these same year-block quintiles. No pair-specific threshold or quintile is permitted.

## 5. Event-level metrics

Compute:

- validation base success rate;
- PR-AUC and relative lift over validation base rate;
- ROC-AUC;
- Brier score;
- primary constant Brier baseline using the observed pooled validation prevalence, which is the best outcome-independent constant-probability benchmark after labels are revealed;
- secondary Brier baseline using the frozen development prevalence `0.16344827586206898`;
- calibration intercept and slope from outcome versus frozen prediction log-odds;
- top-quintile success rate and lift;
- bottom-quintile success rate;
- calibration deciles.

The validation prevalence is used only as an evaluation baseline. It does not update the frozen model.

## 6. Pair-week ranking

For every `instrument × Amsterdam week_key` group:

- select the highest frozen probability;
- break ties by earlier sweep timestamp, then event ID;
- calculate Hit@1;
- calculate the naive within-week random-choice probability;
- calculate regret when a successful alternative existed but the selected candidate failed.

The frozen abstaining selector is applied secondarily:

- retain a pair-week only when its selected candidate probability is at least `0.18252984704127595`;
- report coverage and selected success rate;
- do not recalibrate the threshold;
- abstention performance is diagnostic and not an additional primary validation gate.

## 7. Stable-fingerprint direction test

The five frozen development fingerprints are:

1. `sweep_minute`: expected positive;
2. `t5_reclaim_depth_range_fraction`: expected positive;
3. `t5_mfe_range_fraction`: expected positive;
4. `asian_range_atr20__x__sweep_minute`: expected negative;
5. `sweep_wick_range_fraction`: expected positive.

For each fingerprint:

1. locate its exact transformed feature column in the frozen preprocessor output;
2. rank validation events by that transformed feature value;
3. define low and high groups as the bottom and top validation quartiles, pooled across both years;
4. calculate observed strict-success rate in each group;
5. direction is `POSITIVE` when high-group success exceeds low-group success and `NEGATIVE` when it is lower;
6. an exact tie is `NEUTRAL` and fails preservation.

The gate requires all five observed directions to match their frozen development directions. No significance threshold, alternative binning, pair-specific rescue or substituted fingerprint is permitted.

For diagnosis only, also report frozen-model partial-dependence direction by replacing the exact transformed feature column with its validation 25th and 75th percentiles. Partial dependence does not substitute for the observed direction gate.

## 8. Frozen validation predicates

Every predicate must pass:

1. at least `100` pooled T5 candidates and at least `30` strict successes;
2. EURUSD and GBPUSD each contribute at least `30` candidates;
3. 2022 and 2023 each contribute at least `30` candidates;
4. PR-AUC relative lift over validation base rate is at least `25%`;
5. top-quintile success rate is at least `1.75 ×` validation base rate;
6. bottom-quintile success rate is below validation base rate;
7. pair-week Hit@1 relative lift over the naive baseline is at least `25%`;
8. model Brier score is below the primary validation-prevalence constant baseline;
9. calibration slope is between `0.5` and `1.5`;
10. both pairs show positive top-quintile lift;
11. both years show positive top-quintile lift;
12. all five observed stable-fingerprint directions match development.

## 9. Decisions

Pass:

`PASS_VALIDATION_FREEZE_AUTHORIZE_2024_2025_FINAL_HOLDOUT`

Failure:

`FAIL_VALIDATION_STOP_BEFORE_2024_2025`

On failure, 2024–2025 remains unopened and the fingerprint formulation stops before strategy P&L.

On pass, the identical frozen model and threshold may be applied once to 2024–2025. No refit, feature change, threshold change, weekday removal, pair removal, direction selection or clock narrowing is permitted.

## 10. Evidence requirements

The validation artifact must preserve:

- pair-level event and liquidity ledgers;
- complete frozen prediction ledger;
- all event, pair, year, side and weekday metrics;
- weekly ranking and frozen abstention results;
- all five observed and model-partial-dependence fingerprint direction checks;
- every gate predicate;
- exact model, source-run and commit provenance;
- explicit confirmation that 2024–2025 and strategy P&L remain unopened.
