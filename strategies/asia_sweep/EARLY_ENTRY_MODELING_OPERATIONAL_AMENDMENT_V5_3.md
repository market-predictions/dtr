# Asian Sweep Early-Entry Modeling Operational Amendment v5.3

Date: 2026-07-26  
Branch: `agent/asia-sweep-early-entry-research`

## Status

`FROZEN_BEFORE_AUTHORITATIVE_SOURCE_BACKED_FRONTIER_RUN`

A local implementation dry run was used only to verify runtime and data-shape feasibility. It has no authority to change the following contract, gates or protected partitions.

## Outer evaluation

- development years: 2015–2019;
- five leave-one-year-out outer folds;
- each event receives exactly one out-of-fold probability per landmark and family;
- no threshold or landmark is selected from an outer test year.

## Inner tuning

- three grouped folds inside each outer-training partition;
- grouping key: Amsterdam ISO calendar week;
- EURUSD and GBPUSD events from the same week remain together;
- primary selection metric: log loss;
- secondary tie-breaker: higher PR-AUC.

## Elastic-net family

Estimator: deterministic `SGDClassifier` with logistic loss and elastic-net penalty.

Frozen grid:

- alpha: `0.0001`, `0.0003`, `0.001`;
- L1 ratio: `0.25`, `0.50`;
- maximum iterations: `2000`;
- tolerance: `1e-4`;
- random seed: `20260726`.

Numeric variables are median-imputed with missing indicators and standardized inside each fit. Categorical variables are mode-imputed and one-hot encoded inside each fit.

## Nonlinear challenger

Estimator: `HistGradientBoostingClassifier`.

Frozen grid:

1. learning rate `0.04`, maximum leaves `7`;
2. learning rate `0.08`, maximum leaves `15`.

Fixed values:

- minimum samples per leaf: `45`;
- L2 regularization: `5.0`;
- boosting iterations: `100`;
- random seed: `20260726`.

Numeric variables are median-imputed with missing indicators. Categorical variables are mode-imputed and ordinal-encoded with an explicit unknown value, all inside each fit.

## Calibration

- inner out-of-fold raw probabilities are generated for the selected configuration;
- a logistic Platt calibrator is fit only to those inner out-of-fold probabilities;
- the candidate model is refit on the complete outer-training partition;
- the frozen inner calibrator is then applied to the outer-year probabilities;
- calibration coefficients reported on pooled outer predictions are diagnostic only.

## Quintiles and breadth

- probability quintiles are formed separately inside each held-out calendar year;
- top- and bottom-quintile metrics are therefore not allowed to borrow thresholds across years;
- pair, year, side and weekday breadth are calculated from the same outer predictions;
- pair-week Hit@1 selects the highest probability with deterministic event-ID tie-breaking.

## Legacy benchmark

- `LEGACY_T5` uses the exact frozen development out-of-fold HGB predictions from Actions run `30177831134`;
- it is not refit or recalibrated;
- only its executable geometry is reconstructed at the exact validated snapshot and next active quote.

## Decision authority

The gates and landmark-selection hierarchy remain exactly those in preregistration v5.0. No source-backed result may authorize:

- policy P&L when no pre-T5 candidate passes every gate;
- partial-fraction testing before landmark authorization;
- pair, weekday, side or range-width rescue;
- access to 2020–2025.
