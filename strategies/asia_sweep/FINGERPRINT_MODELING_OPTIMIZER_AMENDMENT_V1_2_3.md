# Asian Sweep Fingerprint Modelling — Optimizer Amendment v1.2.3

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Applies to:

- `FINGERPRINT_MODELING_CONTRACT_V1_2.md`;
- `FINGERPRINT_MODELING_OPERATIONAL_AMENDMENT_V1_2_1.md`;
- `FINGERPRINT_FINAL_FREEZE_AMENDMENT_V1_2_2.md`.

Status: `FROZEN_BEFORE_GROUPED_MODEL_OUTPUT_INSPECTION`

A second score-blind runtime dry run established that nested year-block evaluation of the SAGA implementation remained operationally excessive even after the v1.2.1 grid reduction. The run was terminated before producing a complete hyperparameter table, outer-fold prediction, metric, coefficient, feature ranking or development decision.

This amendment replaces only the optimisation algorithm for the interpretable elastic-net logistic family. Labels, populations, causal features, preprocessing, folds, metrics, selection gates, stable-fingerprint rules, validation partitions and prohibitions remain unchanged.

## 1. Interpretable family

Use scikit-learn `SGDClassifier` as a deterministic optimiser of elastic-net penalised logistic log loss:

- `loss="log_loss"`;
- `penalty="elasticnet"`;
- `average=True`;
- `class_weight=None`;
- `fit_intercept=True`;
- `max_iter=3000`;
- `tol=1e-4`;
- `shuffle=True`;
- `random_state=20260725`.

The model remains an elastic-net logistic classifier. Only the numerical optimisation method changes from batch SAGA to stochastic gradient descent.

## 2. Frozen grid

Replace `C` with the inverse-scale SGD regularisation parameter `alpha`.

Frozen grid:

- `alpha`: `[0.00001, 0.00003, 0.0001, 0.0003, 0.001]`;
- `l1_ratio`: `[0.25, 0.5, 0.75, 1.0]`.

This retains twenty elastic-net configurations across weak to strong regularisation and mixed to sparse penalties.

## 3. Deterministic tie-breaking

For the interpretable family, stronger regularisation means:

1. higher `alpha`;
2. then higher `l1_ratio`;
3. then lexicographic JSON order.

The inner-fold metric hierarchy remains:

1. highest pooled PR-AUC;
2. lower Brier score when PR-AUC differs by less than `0.002`;
3. converged configuration when predictive metrics remain effectively tied;
4. stronger regularisation.

## 4. Final-parameter assembly override

Where v1.2.2 refers to lower `C`, replace that rule with higher `alpha`. All other modal-count and median-rank assembly rules remain binding.

## 5. Acceptance safeguards

Before model output is accepted, CI must prove:

- every grid point uses the frozen SGD configuration;
- identical input order produces identical probabilities;
- deliberate row-order permutation followed by the frozen canonical sort produces identical probabilities;
- every fit converges within `max_iter` or records its iteration exhaustion;
- probabilities are finite and in `[0, 1]`;
- no output from either aborted SAGA dry run is retained.
