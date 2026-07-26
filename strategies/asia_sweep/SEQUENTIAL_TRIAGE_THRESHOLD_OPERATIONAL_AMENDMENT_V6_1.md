# Sequential Triage Threshold and Model Operations — Amendment v6.1

Date: 2026-07-26
State: FROZEN_BEFORE_FORMAL_PHASE_A_DECISION
Branch: `agent/asia-sweep-sequential-triage`

## Purpose

Make the fold-local calibration, model grids, threshold search and deterministic family hierarchy explicit before the formal Phase A decision is accepted.

## Model candidates

The same causal feature contract used by the early-entry frontier is retained.

Primary candidates:
- multinomial elastic-net logistic regression;
- histogram gradient boosting multiclass classifier.

Frozen compact grids:
- elastic net: `C in {0.05, 0.20, 0.80}` and `l1_ratio in {0.25, 0.50}`;
- HGB: `(learning_rate, max_leaf_nodes) in {(0.04, 7), (0.08, 15)}`;
- HGB `min_samples_leaf=45`, `l2_regularization=5.0`, `max_iter=100`.

The compact HGB grid is an operational runtime control, not an outcome-driven model change.

## Grouping and calibration

For every landmark and outer held-out year:
1. use the other four years as training data;
2. tune the candidate model using three Amsterdam-week grouped folds;
3. select hyperparameters by lowest multiclass log loss, with macro one-vs-rest PR-AUC as deterministic tie-break;
4. obtain training-fold out-of-fold probabilities;
5. fit one-vs-rest Platt calibrators on those out-of-fold probabilities and renormalize the three calibrated probabilities to sum to one;
6. fit the selected classifier on the full outer-training population;
7. apply the frozen calibrators and thresholds to the untouched outer year.

No held-out-year outcome may influence calibration, thresholds, margins or model selection.

## Decision rule

For each row, define calibrated probabilities `p_rev`, `p_cont`, and `p_abstain`.

A reversal action is permitted only when:
- `p_rev >= reversal_threshold`;
- `p_rev - p_cont >= conflict_margin`;
- `p_rev >= p_abstain`.

A continuation action is permitted only when:
- `p_cont >= continuation_threshold`;
- `p_cont - p_rev >= conflict_margin`;
- `p_cont >= p_abstain`.

All other rows are `ABSTAIN`. Any theoretical simultaneous pass is resolved to `ABSTAIN`.

## Threshold grid

Training-fold search only:
- reversal threshold: 0.30 to 0.70 in 0.05 increments;
- continuation threshold: 0.30 to 0.70 in 0.05 increments;
- conflict margin: 0.00 to 0.20 in 0.05 increments.

A threshold candidate is eligible only when the training-fold out-of-fold decisions satisfy:
- reversal precision >= 0.40;
- continuation precision >= 0.45;
- at least 20 reversal and 20 continuation decisions;
- abstention coverage between 25% and 75%.

Among eligible candidates, maximize:

`harmonic_mean(reversal_precision, continuation_precision) * sqrt(actionable_coverage) * sqrt(min(class_coverage) / max(class_coverage))`

Tie-breaks, in order:
1. higher minimum directional precision;
2. higher total actionable coverage;
3. smaller conflict margin;
4. lower combined thresholds.

If no training-fold threshold candidate is eligible, that outer fold emits `ABSTAIN` for every event.

## Family hierarchy

Each model family is evaluated as a complete T0–T3 sequence. The interpretable elastic-net sequence is primary when it passes the frozen Phase A gates. HGB may replace it only when elastic net fails, or when HGB improves macro relative PR-AUC lift by at least 0.10 without reducing the lower of reversal and continuation precision.

No per-year or per-row model-family switching is allowed.

## Stop boundary

Phase B realized staged-entry P&L remains blocked unless a complete model-family sequence passes the preregistered Phase A gates. No threshold relaxation, pair rescue or outcome-specific retuning is permitted after the formal run begins.
