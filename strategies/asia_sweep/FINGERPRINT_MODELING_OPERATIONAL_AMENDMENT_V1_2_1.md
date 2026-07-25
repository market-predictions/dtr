# Asian Sweep Fingerprint Modelling — Operational Amendment v1.2.1

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Applies to: `FINGERPRINT_MODELING_CONTRACT_V1_2.md`  
Status: `FROZEN_BEFORE_GROUPED_MODEL_OUTPUT_INSPECTION`

This amendment changes only model-fitting parameters that proved operationally excessive during a score-blind dry run. No grouped out-of-fold score, coefficient, feature importance, weekly-ranking result, development decision, 2022–2023 outcome or 2024–2025 outcome was inspected before this amendment.

The initial dry run established two implementation facts:

1. weakly regularised SAGA fits at `C >= 1.0` frequently exhausted `5000` iterations;
2. the original nested grid would consume disproportionate CI time without adding a distinct scientific hypothesis.

The feature matrices, labels, populations, cross-pair causality, outer and inner year blocks, metrics, model-selection hierarchy, development gate, validation gate and prohibitions remain unchanged.

## 1. Elastic-net override

Replace section 8.1 of the parent contract with:

- solver: `saga`;
- penalty: `elasticnet`;
- no class weighting;
- maximum iterations: `1000`;
- tolerance: `1e-3`;
- deterministic random seed: `20260725`.

Frozen grid:

- `C`: `[0.02, 0.05, 0.1, 0.2, 0.5]`;
- `l1_ratio`: `[0.25, 0.5, 0.75, 1.0]`.

This retains twenty regularised elastic-net configurations spanning strong to moderate regularisation and sparse to mixed penalties. Pure ridge and weakly regularised `C >= 1.0` configurations are removed before output inspection.

A fit reaching `max_iter` is recorded in the tuning audit. It may remain in the grid, but deterministic tie-breaking favours a converged configuration whenever its pooled inner PR-AUC is within `0.002` and its Brier score is not worse by more than `0.001`.

## 2. Histogram-gradient-boosting override

Replace the nonlinear grid with:

- `learning_rate`: `[0.03, 0.06]`;
- `max_leaf_nodes`: `[7, 15]`;
- `min_samples_leaf`: `[20, 50]`;
- `l2_regularization`: `[1.0, 5.0]`;
- maximum iterations: `200`;
- early stopping disabled;
- deterministic random seed: `20260725`.

This retains sixteen nonlinear configurations while removing the most complex 31-leaf trees before output inspection.

## 3. Computational implementation

Within each outer fold:

- each inner-year train/test feature matrix is preprocessed once per landmark and reused across all hyperparameter configurations;
- no preprocessor is shared across different inner training folds;
- logistic configurations may be evaluated in a deterministic warm-start sequence within the same inner fold, ordered from stronger to weaker regularisation;
- resulting probabilities must be equivalent to independently fitted configurations within an absolute tolerance of `1e-5` on synthetic regression tests;
- parallelism may be used only across independent hyperparameter configurations or outer folds and must preserve deterministic output ordering.

These changes reduce repeated computation without changing any training observations, held-out observations, feature values, labels, metrics or selection rules.

## 4. Acceptance tests

Before accepting model output, CI must prove:

- the reduced grids exactly match this amendment;
- a fixed single-fit regression case converges;
- warm-start and independent-fit probabilities agree within the frozen tolerance when warm start is used;
- every inner fold receives its own fitted preprocessor;
- no score from the aborted dry run is retained or used.
