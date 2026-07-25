# Asian Sweep Fingerprint Modelling — Final Freeze Amendment v1.2.2

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Applies to:

- `FINGERPRINT_MODELING_CONTRACT_V1_2.md`;
- `FINGERPRINT_MODELING_OPERATIONAL_AMENDMENT_V1_2_1.md`.

Status: `FROZEN_BEFORE_GROUPED_MODEL_OUTPUT_INSPECTION`

This amendment freezes how outer-fold model-selection results become one executable but non-trading validation model. No grouped out-of-fold score, selected parameter set, coefficient, feature importance, 2022–2023 result or 2024–2025 result was inspected before this rule was committed.

## 1. Final hyperparameter assembly

After a landmark/model-family candidate passes every development-eligibility predicate and the deterministic candidate-selection hierarchy selects it:

1. collect the seven hyperparameter sets selected independently inside the seven outer folds;
2. choose the modal exact parameter set;
3. when multiple parameter sets have the same modal count, choose the set with the best median rank across the seven outer-fold inner-tuning tables;
4. when still tied, choose stronger regularisation:
   - elastic net: lower `C`, then higher `l1_ratio`;
   - histogram gradient boosting: fewer leaf nodes, larger `min_samples_leaf`, larger `l2_regularization`, then lower learning rate;
5. use lexicographic JSON order as the final deterministic tie-break.

No pooled outer-test metric is used to select final hyperparameters beyond selecting the candidate family and landmark under the already frozen hierarchy.

## 2. Full-development fit

The final validation bundle is fitted once on all eligible 2015–2021 events for the selected landmark using:

- the exact frozen feature manifest;
- one preprocessor fitted only on 2015–2021;
- the final hyperparameters selected by section 1;
- the frozen random seed;
- no refitting to 2022–2025.

The bundle must contain:

- landmark and family;
- ordered numeric, categorical and interaction feature names;
- imputation, missing-indicator, robust-scaling and one-hot-encoding state;
- fitted classifier;
- selected development abstention threshold, or explicit `NO_ABSTENTION_THRESHOLD`;
- five stable fingerprint names and expected directions;
- source run and commit provenance;
- development population counts and base rate.

## 3. Serialization and validation use

The final bundle is serialized with `joblib` and uploaded as a compact development artifact. The 2022–2023 workflow must load this exact bundle and may not:

- fit or update preprocessing;
- fit or update the classifier;
- recalculate the abstention threshold;
- reorder, add or remove features;
- replace stable fingerprints;
- select another landmark, model family, pair, direction, weekday or clock window.

Unknown categorical values are handled only by the already frozen `handle_unknown=ignore` encoder behavior. Missing values use the frozen development medians and indicators.

## 4. Failure behavior

If no model candidate passes development eligibility:

- no validation bundle is written;
- decision is `FAIL_DEVELOPMENT_STOP_BEFORE_2022_2023`;
- the 2022–2023 workflow remains absent or disabled;
- 2024–2025 and strategy P&L remain unopened.

If a nonlinear challenger is selected but five stable directional fingerprints cannot be established under the parent contract, that challenger is ineligible for final selection even when its predictive metrics pass.
