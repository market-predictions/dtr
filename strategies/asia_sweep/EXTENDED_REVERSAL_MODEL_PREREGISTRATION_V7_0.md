# Asian Sweep Extended-Reversal Model — Preregistration v7.0

Date: 2026-07-26
State: FROZEN_BEFORE_TARGET LABELS AND MODEL SCORES
Branch: `agent/asia-sweep-extended-reversal`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025

## Decision problem

The validated midpoint model does not answer whether a reversal will extend to a large directional objective. This programme predicts extended reversal outcomes directly from causal T0–T3 information and the actual executable reversal entry at each landmark.

No model, filter or position structure may use midpoint success as the target.

## Reversal direction and entry

- upper Asian-range sweep: reversal short;
- lower Asian-range sweep: reversal long;
- entry: first active BID/ASK open after each T0, T1, T2 or T3 landmark;
- long entry uses ASK; short entry uses BID;
- adverse stop: `0.20 * Asian range` beyond the sweep extreme;
- events already resolved before a landmark remain excluded under the immutable early-entry ledger;
- same-minute stop/target ambiguity is stop-first.

## Frozen target labels

### `EXT_FIXED_2R_1100`

Reach 2R from the executable landmark entry before the adverse stop and before 11:00 Amsterdam.

### `EXT_FIXED_3R_1200`

Reach 3R before stop and before 12:00 Amsterdam.

### `EXT_FIXED_4R_1400`

Reach 4R before stop and before 14:00 Amsterdam.

### `EXT_OPPOSITE_BOUNDARY_1100`

Reach the opposite Asian-range boundary before stop and before 11:00 Amsterdam:
- lower sweep reversal long: Asian high;
- upper sweep reversal short: Asian low.

### `EXT_OPPOSING_LIQUIDITY_1400`

Reach the nearest confirmed external-liquidity level in the reversal direction before stop and before 14:00 Amsterdam:
- lower sweep reversal long: nearest available HIGH level beyond entry;
- upper sweep reversal short: nearest available LOW level beyond entry.

The target must be beyond the executable entry and produce positive reward/risk. Otherwise the event is ineligible for that target.

## Causal feature contract

The exact early-entry feature set is reused at each landmark. No future T2/T3 feature is backfilled into T0/T1. Cross-pair state uses only observations available by the landmark timestamp.

## Model families

Primary:
- elastic-net logistic regression with fold-local imputation, scaling and categorical encoding.

Challenger:
- histogram gradient boosting with fold-local imputation and ordinal categorical encoding.

The compact hyperparameter grids and grouped fitting procedure match the frozen early-entry research environment. Each target/landmark/family receives separate leave-one-year-out predictions with Amsterdam-week grouped inner tuning and fold-local Platt calibration.

## Candidate gates

A target/landmark/family candidate passes only when:

- at least 400 eligible events and 75 positive target cases;
- PR-AUC relative lift over base rate >=50%;
- top-decile target rate >=2.00x base rate;
- bottom-decile target rate <=0.60x base rate;
- calibrated Brier score below the constant class-frequency Brier;
- positive top-decile lift in both pairs and at least four of five years;
- median top-decile stressed reward/risk >=1.50;
- at least 75% of top-decile candidates retain >=1.25R under +0.10-pip entry/stop stress;
- median top-decile stressed expected-value proxy >0R;
- no pair, year, weekday or sweep-direction concentration above 70%;
- at least 50 top-decile cases.

The expected-value proxy is:

`calibrated_target_probability * stressed_RR - (1 - calibrated_target_probability)`

It is a geometry diagnostic, not realized P&L.

## Landmark and family selection

For each target:

1. identify the earliest passing elastic-net landmark;
2. identify the earliest passing HGB landmark;
3. use elastic net when it passes;
4. HGB may replace elastic net only when it improves PR-AUC relative lift by at least 0.15 without reducing top-decile target rate or stressed expected-value proxy;
5. a later landmark may replace an earlier passing landmark only when PR-AUC relative lift improves by at least 0.20 and median stressed R:R declines by no more than 0.20R.

No year-specific, pair-specific or row-specific family/landmark switching is allowed.

## Primary target hierarchy

The target programme is not allowed to choose the best pooled result after inspection. The first target with a passing selected model in this economic hierarchy becomes the primary target:

1. `EXT_FIXED_3R_1200`;
2. `EXT_FIXED_4R_1400`;
3. `EXT_FIXED_2R_1100`;
4. `EXT_OPPOSING_LIQUIDITY_1400`;
5. `EXT_OPPOSITE_BOUNDARY_1100`.

The 3R target is primary because it balances extension and attainable frequency. Four-R is preferred over 2R only when 3R fails, preserving the explicit let-winners-run hypothesis. Structural targets are fallback targets rather than post-hoc replacements.

## Authorization boundary

If no target has a passing selected model:

`FAIL_EXTENDED_REVERSAL_MODEL_STOP_BEFORE_POSITION_STRUCTURE_PNL`

If a primary target passes:

`PASS_EXTENDED_REVERSAL_MODEL_AUTHORIZE_POSITION_STRUCTURE_DISCOVERY`

Only the latter authorizes comparison of:

- `TP1_50_RUNNER_50`;
- `TP1_25_RUNNER_75`;
- `NO_TP1_FULL_RUNNER`.

The three structures must use identical frozen entries, stop, primary target, horizon and candidate threshold. No structure-specific signal or landmark is allowed.

## Position-structure discovery boundary

When authorized, structure discovery uses nested leave-one-year-out selection and actual BID/ASK paths. The midpoint partial is executed only if reached before the primary target/stop/horizon. Runner stop-management variants are not added in this first comparison; the common stop remains fixed. Break-even may be researched only in a later separately preregistered challenger.

## Stop rules

- no target, horizon, stop, model grid, landmark rule or hierarchy change after this preregistration;
- no 2020–2025 access before a complete frozen development decision;
- no pair/day/direction/weekday rescue;
- no importing a continuation or staged-reversal result;
- no Pine, alerts, paper trading or deployment.
