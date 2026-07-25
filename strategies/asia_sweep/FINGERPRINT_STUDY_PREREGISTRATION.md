# Asian Sweep Success/Failure Fingerprint Study — Preregistration

Version: `v1.0.0`  
Date frozen: `2026-07-25`  
Branch: `agent/asia-sweep-fingerprint-study`  
Status: `FROZEN_BEFORE_FEATURE_OUTCOME_INSPECTION`

## 1. Research objective

The purpose of this programme is not to retest whether the average Asian-range sweep reverses. It is to determine whether successful reversals can be distinguished from failed sweeps using information that is available before the eventual outcome.

The primary questions are:

1. How often does each EURUSD and GBPUSD calendar week contain at least one successful Asian-range reversal during the Amsterdam morning window?
2. What path types occur after an Asian-range sweep: immediate continuation, false reversal, stalled reaction, sustained partial reversal, midpoint reversal, or full-range reversal?
3. Which causal fingerprints distinguish successful midpoint reversals from failed sweeps?
4. Can a frozen model rank the most promising sweep candidate within each pair-week on unseen years?
5. Do the fingerprints remain stable across EURUSD, GBPUSD, weekdays, years, sweep directions, and volatility regimes?

The programme is diagnostic and predictive. Strategy entries, stops, targets, transaction costs, R multiples, P&L, Pine implementation, alerts, sizing and deployment remain blocked until the fingerprint model passes unseen validation.

## 2. Scientific boundary and partitions

The prior broad ten-pair and narrow Amsterdam-window studies exposed aggregate outcomes through 2021. Therefore 2015–2021 is treated as model-development evidence, not untouched confirmation evidence.

Frozen partitions:

- `2015–2021`: feature discovery, failure taxonomy, grouped cross-validation and model development;
- `2022–2023`: first untouched fingerprint-validation partition;
- `2024–2025`: final untouched holdout;
- `2026 YTD`: monitoring only.

No 2022–2025 outcome may be inspected until the feature set, labels, models, hyperparameter grids and validation gates are frozen.

## 3. Market clock

All time boundaries are native `Europe/Amsterdam` timezone boundaries and use the timezone database.

Primary clocks:

- Asian reference range: `[00:00, 08:00)` Amsterdam;
- sweep-candidate window: `[08:00, 10:00)` Amsterdam;
- ICT reversal window: `[09:00, 10:00)` Amsterdam;
- post-window follow-through audit: `[10:00, 11:00)` Amsterdam.

The reference range is no longer inferred through fixed New York hours. This avoids one-hour distortions during Europe/United States daylight-saving mismatch weeks.

## 4. Primitive sweep universe

The existing `REJECTION` label is not used to define the candidate universe because the purpose of the study is to discover which sweep and reclaim structures matter.

For each pair and Amsterdam date:

1. Build the completed active midpoint Asian high, low and range from `[00:00, 08:00)`.
2. Require at least 456 active one-minute observations of the expected 480 minutes.
3. Require a strictly positive Asian range.
4. From 08:00 through 09:59, identify the first active midpoint breach of each side:
   - upper sweep: midpoint high exceeds the Asian high;
   - lower sweep: midpoint low falls below the Asian low.
5. A breach must exceed the boundary by at least the larger of:
   - one pair pip;
   - `0.02 × Asian range`.
6. Retain at most one first sweep per side and date.
7. A one-minute bar that sweeps both boundaries is classified as `two_sided_ambiguous` and excluded from the primary binary model while retained in the anatomy ledger.

This universe allows the sweep to occur before 09:00 and the reversal to begin during 09:00–10:00, which matches the stated time-and-price hypothesis more closely than requiring the detector confirmation itself to occur in the hour.

## 5. Frozen outcome taxonomy

All distances are normalized by the completed Asian-range width. All paths are evaluated using active midpoint prices.

### 5.1 Primary success label

`MIDPOINT_SUCCESS_09_10` is true when all predicates hold:

1. the sweep occurs before 10:00 Amsterdam;
2. after the sweep, price reaches the Asian-range midpoint at or before 10:00 Amsterdam;
3. the midpoint is reached before price extends an additional `0.20 × Asian range` beyond the sweep extreme;
4. the event is not two-sided ambiguous.

The first-passage ordering is authoritative. The label does not require a preselected reclaim candle, market-structure-shift rule or entry model.

### 5.2 Secondary path labels

Secondary labels are descriptive and cannot replace the primary label after results are seen:

- `REACTION_25`: favorable excursion reaches `0.25 × range` before the adverse continuation barrier;
- `FULL_RANGE_SUCCESS`: opposite Asian boundary is reached by 11:00 before the adverse continuation barrier;
- `LATE_MIDPOINT`: midpoint is not reached by 10:00 but is reached between 10:00 and 11:00;
- `IMMEDIATE_CONTINUATION`: adverse continuation barrier is reached before `0.25 × range` favorable excursion;
- `FALSE_REVERSAL`: `0.25 × range` favorable excursion occurs, midpoint is not reached by 10:00, and the adverse barrier is subsequently reached by 11:00;
- `STALLED_REACTION`: neither midpoint nor adverse barrier is reached by 11:00;
- `TWO_SIDED_AMBIGUOUS`: both Asian boundaries are swept before a primary outcome resolves.

For every event, record first-passage timestamps, 5/15/30/60-minute signed returns, MFE, MAE, midpoint hit, opposite-boundary hit and close location at 10:00 and 11:00.

## 6. Two causal decision checkpoints

### 6.1 T0 — sweep-time model

The T0 model may use only information known by the close of the first sweep minute.

Its purpose is to answer: `given that a sweep has just occurred, is this context more likely to produce a successful reversal?`

### 6.2 T5 — confirmation model

The T5 snapshot is fixed at five minutes after the first sweep timestamp.

The T5 model may use information through that timestamp only. The primary T5 target is still midpoint success, but any midpoint reached before the T5 snapshot is excluded from T5 modelling because the outcome has already occurred.

Its purpose is to answer: `after observing the first five minutes of sweep/reclaim behaviour, can true reversals be distinguished from false or continuation sweeps?`

T0 and T5 are separate models. A T5 feature may not be presented as a T0 fingerprint.

## 7. Frozen feature families

All features must be deterministic, causal and defined before validation outcomes are opened.

### 7.1 Time and calendar

- pair;
- weekday;
- exact sweep minute within the 08:00–10:00 window;
- before/after 09:00 flag;
- 09:00–09:29 versus 09:30–09:59;
- daylight-saving mismatch-week flag;
- week of month.

### 7.2 Asian-range structure

- range width in pips;
- 20-day and 60-day range percentile;
- Asian close location within the range;
- net Asian-session return divided by range;
- realized one-minute volatility;
- high-formation time and low-formation time;
- number of distinct high-zone and low-zone touches;
- number of direction changes;
- first half versus second half range expansion;
- whether both extremes formed early or late;
- range symmetry and close-to-midpoint distance.

### 7.3 Pre-sweep London path

- 08:00-to-sweep signed return;
- pre-sweep MFE and MAE relative to each Asian boundary;
- realized volatility from 08:00 to sweep;
- distance from Amsterdam midnight open;
- distance from 08:00 open;
- whether the opposite boundary was previously touched or swept;
- number of boundary tests before the qualifying sweep;
- speed from 08:00 to sweep;
- compression or expansion immediately before the breach.

### 7.4 Sweep anatomy at T0

- upper versus lower sweep;
- breach depth in pips and range fractions;
- one-minute wick/body geometry;
- close location relative to the swept boundary;
- close location within the sweep bar;
- displacement size relative to trailing volatility;
- spread and quote-activity measures when source fields permit;
- external liquidity confluence with prior-day and prior-week highs/lows;
- whether EURUSD and GBPUSD sweep the same USD direction within a 15-minute interval;
- cross-pair SMT divergence: one pair sweeps while the other does not or fails to confirm.

### 7.5 Five-minute confirmation anatomy at T5

- elapsed minutes outside the Asian range;
- number of closes outside and inside;
- reclaim achieved flag and reclaim delay;
- depth of close back inside the range;
- five-minute favorable and adverse excursion;
- five-minute signed return;
- sweep extreme extension after the first breach;
- retest of the swept boundary;
- retest hold/fail result;
- break of the last causal one-minute and five-minute swing opposite the sweep;
- displacement away from the sweep extreme;
- imbalance/FVG descriptors only when defined mechanically from completed bars;
- cross-pair relative-strength divergence through T5.

### 7.6 Higher-timeframe context

Using only completed information before the sweep:

- prior-day high/low and close location;
- prior-week high/low;
- distance to prior-day and prior-week liquidity;
- daily opening direction;
- trailing daily ATR percentile;
- prior-day directional return;
- current week position and weekly opening direction.

No manually assigned narrative bias is permitted.

## 8. Failure-fingerprint analysis

The development report must compare successful midpoint reversals against each failure class separately, not only against one pooled failure bucket.

Required comparisons:

- success versus immediate continuation;
- success versus false reversal;
- success versus stalled reaction;
- success versus late midpoint;
- success versus two-sided ambiguity.

For every feature, report:

- event counts and missingness;
- median and interquartile range by class;
- standardized mean or rank effect;
- monotonic-bin success rates;
- pair-stratified and year-stratified results;
- calendar-week clustered uncertainty;
- false-discovery-rate-adjusted exploratory p-values.

No feature is promoted solely because it produces a low unadjusted p-value.

## 9. Predictive models

Two primary model families are frozen:

1. elastic-net logistic regression for interpretable stable coefficients;
2. histogram gradient boosting as a nonlinear challenger.

The models must use identical frozen labels and causal feature matrices.

Development evaluation uses nested grouped cross-validation:

- outer grouping: Amsterdam calendar week;
- year blocks must remain intact where feasible;
- EURUSD and GBPUSD events from the same date remain in the same fold;
- no random event-level split;
- preprocessing, missing-value handling, feature selection and hyperparameter fitting occur inside each training fold.

The final development model is frozen before opening 2022–2023.

## 10. Primary prediction objective

The primary operational objective is pair-week ranking, not indiscriminate event classification.

For each EURUSD and GBPUSD calendar week containing at least one candidate sweep, rank candidates by predicted midpoint-success probability.

Required metrics:

- base success rate;
- PR-AUC and ROC-AUC;
- Brier score and calibration slope/intercept;
- top-quintile success rate and lift versus base;
- bottom-quintile success rate;
- `Hit@1`: proportion of pair-weeks where the highest-ranked candidate is successful;
- opportunity coverage: proportion of pair-weeks for which a candidate is selected;
- successful-pair-week coverage: proportion of pair-weeks that actually contain at least one success;
- regret: successful weeks in which the model selected a failed candidate despite a successful alternative.

This directly tests the observation that approximately one usable reversal may exist per pair-week.

## 11. Validation gate on 2022–2023

The fingerprint programme advances only if every primary predicate passes on untouched 2022–2023 data:

1. at least 100 pooled candidate sweeps and at least 30 midpoint successes;
2. both EURUSD and GBPUSD contribute at least 30 candidates;
3. both 2022 and 2023 contribute at least 30 candidates;
4. frozen model PR-AUC exceeds the base success rate by at least 25% relative lift;
5. top-quintile success rate is at least 1.75 times the full-sample base rate;
6. bottom-quintile success rate is below the full-sample base rate;
7. pair-week `Hit@1` exceeds the naive candidate-choice baseline by at least 25% relative lift;
8. Brier score improves on the constant-probability baseline;
9. calibration slope is between 0.5 and 1.5;
10. both pairs show positive top-quintile lift;
11. both years show positive top-quintile lift;
12. the five highest-ranked stable fingerprints preserve the same direction as in grouped development analysis.

Failure stops this fingerprint formulation before 2024–2025 and before strategy P&L.

## 12. Final holdout gate on 2024–2025

Only after the 2022–2023 validation gate passes may the frozen model be applied once to 2024–2025.

The final holdout must preserve:

- positive PR-AUC lift;
- positive top-quintile lift;
- positive `Hit@1` lift;
- positive results on both pairs;
- positive results in both years;
- acceptable calibration;
- stable fingerprint direction.

No refitting, threshold adjustment, weekday removal, pair removal or feature substitution is allowed after 2022–2023 is opened.

## 13. Weekly-frequency claim

The claim that each pair produces at least one successful reversal per week is tested descriptively before modelling.

For each pair, report:

- total pair-weeks;
- pair-weeks with at least one candidate sweep;
- pair-weeks with at least one midpoint success;
- success-week proportion and Wilson interval;
- distribution of zero, one, two and more successes per week;
- weekday distribution of the first weekly success.

The claim is not assumed true and is not used to force a model-selection threshold.

## 14. Explicit prohibitions

Until the fingerprint validation and final holdout gates pass, the programme may not:

- calculate executable strategy P&L;
- optimize stops, targets or risk/reward ratios;
- remove weekdays after seeing validation outcomes;
- select EURUSD or GBPUSD individually after seeing validation outcomes;
- select upper or lower sweeps retrospectively;
- narrow 09:00–10:00 into smaller clock windows after seeing outcomes;
- introduce discretionary ICT labels;
- inspect 2024–2025 early;
- build Pine, alerts, sizing, paper trading or deployment.

The purpose is to discover and validate causal fingerprints, not to guarantee preservation of the Asian Sweep idea.