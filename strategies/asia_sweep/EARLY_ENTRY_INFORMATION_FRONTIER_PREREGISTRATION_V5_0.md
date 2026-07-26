# Asian Sweep Early-Entry Information Frontier — Preregistration v5.0

Date: 2026-07-26  
Branch: `agent/asia-sweep-early-entry-research`

## Objective

Determine whether causal information available at T0, T1, T2 or T3 can identify successful Asian Sweep reversals early enough to preserve materially better executable reward/risk than the validated T5 decision.

This first phase is an information-versus-payoff study. It does not optimize a trading policy or inspect strategy P&L.

## Scientific boundary

The following findings remain fixed:

- the T5 reversal fingerprint is predictive and validated;
- post-T5 midpoint execution failed because confirmation arrived after substantial favorable movement;
- the long-runner grid failed nested out-of-fold selection;
- no runner policy from that grid may be carried into this programme.

The Asian midpoint is used here as the first objective and causal outcome landmark, not asserted to be the final position target.

## Universe and clock

- EURUSD and GBPUSD;
- Asian range `[00:00, 08:00)` Europe/Amsterdam;
- primitive sweeps `[08:00, 10:00)`;
- reversal direction is opposite the swept boundary;
- landmarks: T0, T1, T2, T3 and T5, where Tk means k completed M1 bars after the sweep bar;
- actual qualified Dukascopy BID/ASK M1 data.

## Development and protected partitions

- landmark discovery: 2015–2019;
- first execution-policy validation: 2020–2021, unopened during this phase;
- execution holdout 1: 2022–2023, unopened;
- execution holdout 2: 2024–2025, unopened.

The landmark study may inspect only 2015–2019 feature/outcome data. No 2020–2025 early-entry feature, score, fill or P&L result may be opened.

## Landmark population

At landmark Tk an event is eligible only when:

- the primitive sweep has occurred;
- k complete active M1 bars are available after the sweep;
- the Asian midpoint has not already been reached;
- the original adverse-continuation barrier has not already been reached;
- the current executable entry lies between the midpoint and adverse barrier;
- the event remains before 10:00 Amsterdam;
- no feature uses information after the landmark close.

Population attrition between landmarks must be reported explicitly. Resolved events are not silently treated as model failures.

## Frozen causal outcome

Primary outcome:

> After the landmark, does price reach the Asian midpoint before the original adverse barrier and before 10:00 Amsterdam?

The path begins strictly after the landmark bar closes. Same-bar outcome information cannot enter the label for that landmark.

Secondary diagnostics:

- midpoint before adverse barrier within 30 minutes of the landmark;
- midpoint before adverse barrier within 60 minutes;
- favorable and adverse excursion after entry;
- post-midpoint continuation excursion through 12:00, 14:00, 16:00 and 18:00.

Secondary diagnostics have no model-selection or runner-policy authority.

## Executable geometry snapshot

At every eligible landmark, record:

- executable market entry at the first active minute open strictly after the landmark;
- initial stop at the frozen adverse barrier;
- TP1 at the Asian midpoint;
- current entry-to-stop risk;
- remaining entry-to-midpoint reward;
- executable reward/risk;
- spread in pips and as a fraction of initial risk;
- whether the entry geometry is still valid under 0.10-pip stress.

No order is actually simulated in this phase beyond measuring the causal entry price and subsequent path outcome.

## Feature blocks

### T0 context and sweep mechanics

- Amsterdam sweep timestamp and minute bucket;
- upper versus lower sweep;
- Asian-range pips, ATR/ADR normalization and rolling percentile;
- sweep depth, speed, body and wick fractions;
- pre-sweep approach return and volatility;
- Asian close location and range formation timing;
- layered-liquidity counts, consumed stack and residual same-side liquidity;
- opposing-side destination liquidity;
- prior-day, prior-New-York, prior-week, M15/H1 pivot and equal-high/low topology;
- causal EURUSD/GBPUSD cross-pair state.

### T1–T3 incremental price response

Using only completed bars through the landmark:

- closes outside versus inside the Asian range;
- reclaim flag, delay and depth;
- favorable and adverse excursion;
- net displacement from sweep extreme;
- boundary retest, hold or failure;
- short-term swing break away from the sweep;
- continued same-side liquidity consumption;
- cross-pair confirmation or divergence through the same landmark.

### T5 benchmark

- the exact validated T5 model probability is included as a benchmark only;
- no T5 feature or score may be backfilled into T0–T3 rows.

## Model family

For each of T0, T1, T2 and T3:

1. primary: elastic-net logistic regression;
2. challenger: shallow histogram-gradient-boosting classifier.

The existing frozen T5 HGB model is not refit and serves only as a benchmark.

All preprocessing, feature selection, imputation and calibration occur inside grouped folds.

## Cross-validation

Use five leave-one-year-out outer folds across 2015–2019.

Within each outer fold:

- inner folds are grouped by Amsterdam calendar week;
- same-date EURUSD and GBPUSD events remain in the same group;
- hyperparameters are selected by log loss, with PR-AUC as a secondary metric;
- calibration is fit only on inner training predictions;
- no threshold or landmark is selected using the held-out year.

## Information-payoff frontier

For each landmark and model, report out-of-fold:

- eligible event count and success base rate;
- PR-AUC and lift over base rate;
- ROC-AUC;
- Brier score and constant baseline;
- calibration slope and intercept;
- top- and bottom-quintile success rates;
- pair, year, sweep-side and weekday breadth;
- median and quartiles of executable reward/risk;
- median spread/risk;
- top-quintile reward/risk;
- fraction of candidates with reward/risk at least 1.0, 1.5 and 2.0;
- expected-value proxy `p × reward/risk − (1 − p)` without treating it as realized P&L;
- pair-week ranking and abstention diagnostics.

## Landmark viability gate

A pre-T5 landmark is viable for a later execution-policy amendment only if its out-of-fold evidence satisfies all:

- at least 400 eligible events pooled;
- at least 150 events per pair;
- PR-AUC lift over base at least 50%;
- top-quintile success at least 1.75× base rate;
- bottom-quintile success below 0.60× base rate;
- Brier score better than the constant baseline;
- positive top-quintile lift on both pairs;
- positive top-quintile lift in at least four of five years;
- median executable reward/risk in the top quintile at least 1.00;
- at least 35% of top-quintile candidates retain reward/risk at least 1.50;
- median expected-value proxy in the top quintile greater than zero under 0.10-pip stress;
- no single weekday, pair or sweep side contributes more than 70% of top-quintile successes.

## Landmark selection hierarchy

- select the earliest landmark passing every viability gate;
- a later landmark may replace it only when PR-AUC lift improves by at least 20 percentage points while median top-quintile reward/risk declines by no more than 0.20;
- ties favor the earlier landmark and the simpler elastic-net model;
- no realized P&L is used in landmark selection.

If no T0–T3 landmark passes, stop early-entry research before policy simulation.

## Conditional execution-policy amendment

Only after a landmark passes may a new binding amendment define:

- probability/expected-value threshold;
- full versus provisional position size;
- add, retain, reduce or cancel logic at later landmarks;
- exact entry fill;
- fixed payoff geometry selected independently of the failed runner grid;
- discovery and validation P&L gates.

No policy P&L may be inspected before that amendment is committed.

## Explicit prohibitions

- no use of the final T5 score at T0–T3;
- no pair, weekday, year, side or range-width rescue;
- no runner target or horizon selection in this phase;
- no partial-fraction optimization;
- no use of pooled best-looking landmark without outer-fold evidence;
- no opening 2020–2025;
- no Pine, alerts, paper trading or deployment.

## Required outputs

- landmark-level causal event ledger;
- feature audit and future-append invariance tests;
- out-of-fold predictions for every landmark/model;
- information-payoff frontier report;
- pair/year/side/weekday stability tables;
- selected-landmark decision or stop decision;
- roadmap, changelog and independent reconstruction.
