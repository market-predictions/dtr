# Asian Sweep Fingerprint Modelling — Nonlinear Challenger Amendment v1.2.4

Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Status: `FROZEN_BEFORE_GROUPED_MODEL_OUTPUT_INSPECTION`

A score-blind runtime dry run showed that the previous sixteen-configuration histogram-gradient-boosting grid was disproportionate for seven outer years × six inner years × two landmarks. The run was terminated before a complete tuning table, outer-fold prediction ledger, feature importance or development decision existed.

This amendment constrains only the nonlinear challenger. The primary elastic-net logistic family, all labels, causal feature matrices, folds, metrics, gates and validation boundaries remain unchanged.

## Frozen nonlinear family

Use scikit-learn `HistGradientBoostingClassifier` with:

- `loss="log_loss"`;
- `early_stopping=False`;
- `max_iter=120`;
- `random_state=20260725`.

Frozen four-point grid:

1. `learning_rate=0.04`, `max_leaf_nodes=7`, `min_samples_leaf=50`, `l2_regularization=5.0`;
2. `learning_rate=0.08`, `max_leaf_nodes=7`, `min_samples_leaf=50`, `l2_regularization=5.0`;
3. `learning_rate=0.04`, `max_leaf_nodes=15`, `min_samples_leaf=50`, `l2_regularization=5.0`;
4. `learning_rate=0.08`, `max_leaf_nodes=15`, `min_samples_leaf=50`, `l2_regularization=5.0`.

The challenger therefore tests shallow versus moderately complex nonlinear structure and slower versus faster shrinkage while holding leaf support and regularisation conservatively fixed.

## Tie-breaking

When nonlinear configurations are predictively tied under the parent metric hierarchy, prefer:

1. fewer leaf nodes;
2. lower learning rate;
3. lexicographic JSON order.

## Scientific boundary

The nonlinear challenger cannot be selected merely because it fits development data more closely. It must still pass every frozen development predicate, establish five stable directional fingerprints, and beat or materially separate from the interpretable family under the existing deterministic hierarchy.
