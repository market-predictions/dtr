# Asian Sweep Fingerprint Study — Final Holdout Contract v1.4

Date frozen: `2026-07-26`  
Branch: `agent/asia-sweep-fingerprint-study`  
Status: `FROZEN_BEFORE_2024_2025_OUTCOME_INSPECTION`

## 1. Objective

Apply the exact frozen Asian Sweep T5 reversal classifier once to the untouched 2024–2025 EURUSD and GBPUSD period.

No model fitting, recalibration, threshold adjustment, feature substitution, pair selection, weekday selection, direction selection, clock-window change or label change is permitted.

## 2. Immutable provenance

- development anatomy run: `30174245825`;
- frozen development model run: `30177831134`;
- untouched validation run: `30178537776`;
- selected landmark: `T5`;
- selected family: histogram gradient boosting;
- parameters: `learning_rate=0.04`, `max_leaf_nodes=7`, `min_samples_leaf=50`, `l2_regularization=5.0`, `max_iter=120`;
- frozen pair-week abstention threshold: `0.18252984704127595`;
- pinned scikit-learn version: `1.9.0`.

## 3. Holdout population

- pairs: EURUSD and GBPUSD;
- years: 2024 and 2025 only;
- candidate sweep range: `[08:00, 10:00)` Europe/Amsterdam;
- T5 population: candidates still unresolved five completed minutes after the sweep under the frozen landmark rules;
- target: strict Asian midpoint success inside `[09:00, 10:00)` before the frozen adverse-continuation barrier.

No 2024–2025 event or outcome may be used before this contract, implementation and tests are committed.

## 4. Frozen evaluation

Predictions use the exact serialized development preprocessor and classifier. Quintiles and deciles are assigned independently within each holdout year, with deterministic event-ID tie-breaking. Pair-week ranking and abstention use the unchanged development threshold.

The five frozen fingerprint directions are:

1. `sweep_minute`: positive;
2. `t5_reclaim_depth_range_fraction`: positive;
3. `t5_mfe_range_fraction`: positive;
4. `asian_range_atr20__x__sweep_minute`: negative;
5. `sweep_wick_range_fraction`: positive.

## 5. Final holdout predicates

All predicates must pass:

1. at least 100 pooled T5 candidates and at least 30 strict successes;
2. both pairs contribute at least 30 candidates;
3. both 2024 and 2025 contribute at least 30 candidates;
4. PR-AUC exceeds the holdout base rate by at least 25% relative lift;
5. top-quintile success rate is at least 1.75 times the holdout base rate;
6. bottom-quintile success rate is below the holdout base rate;
7. pair-week Hit@1 exceeds the naive candidate-choice baseline by at least 25% relative lift;
8. Brier score improves on the constant holdout-prevalence baseline;
9. calibration slope is between 0.5 and 1.5;
10. both EURUSD and GBPUSD show positive top-quintile lift;
11. both 2024 and 2025 show positive top-quintile lift;
12. all five frozen fingerprints preserve their observed direction.

Pass decision:

`PASS_FINAL_HOLDOUT_AUTHORIZE_EXECUTABLE_STRATEGY_RESEARCH`

Failure decision:

`FAIL_FINAL_HOLDOUT_STOP_ASIAN_SWEEP_FINGERPRINT_PROGRAMME`

Failure blocks strategy P&L and prohibits rescue through pair/day/direction selection, refitting, recalibration or threshold changes.

## 6. Boundary after a pass

A pass authorizes a separate executable-strategy research stage. It does not establish profitability and does not authorize deployment. The subsequent stage must freeze entry timing, spread/slippage treatment, stops, targets, overlapping signals, trade management and risk sizing before P&L is inspected.

## 7. Continuation-hypothesis separation

The proposed continuation/fake-rejection model is scientifically plausible but is not part of this holdout. A low reversal probability is not treated as a continuation signal because the complementary population also contains stalled reactions, early/late reversals and ambiguous paths.

The continuation hypothesis is recorded separately in `FINGERPRINT_CONTINUATION_TRIAGE_ROADMAP.md`. Opening 2024–2025 here means those years cannot later be represented as untouched evidence for that new hypothesis.