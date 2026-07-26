# Asian Sweep Executable Reversal Strategy — Discovery Decision

Date: `2026-07-26`  
Work package: `AS-WP-20260726-11`  
Actions run: `30192167763`  
Evaluated head: `60a34be62af49b01b874d842fea73ddcd28b8ad9`  
Decision artifact: `sha256:66193c9ef92d213aae5e6cde732204746fd620b6a4095990bcfb58b4064a749a`

## Decision

`FAIL_DISCOVERY_STOP_BEFORE_EXECUTION_VALIDATION`

No preregistered entry variant converted the validated T5 reversal fingerprint into a positive, stable and spread-aware executable strategy during 2015–2019.

The 2020–2021 execution validation, 2022–2023 execution holdout and 2024–2025 final execution holdout remain unopened. No portfolio P&L, position sizing, Pine, alerts, paper trading or deployment is authorised.

## Frozen setup

The discovery used:

- EURUSD and GBPUSD;
- Asian range `[00:00, 08:00)` Europe/Amsterdam;
- candidate sweeps `[08:00, 10:00)`;
- the exact frozen T5 histogram-gradient-boosting model;
- out-of-fold 2015–2019 predictions;
- probability threshold `0.18252984704127595`;
- one filled trade maximum per pair per Amsterdam date;
- actionable entry strictly after the fifth completed minute;
- actual qualified Dukascopy BID/ASK M1 data;
- target at the Asian midpoint;
- stop at the original adverse barrier, `0.20 × Asian range` beyond the sweep extreme;
- time exit before 10:00 Amsterdam;
- conservative stop-first ordering for same-bar stop/target touches;
- spread embedded in BID/ASK execution;
- additional `0.10` and `0.25` pip slippage stresses.

No model refit, threshold change, pair/day/direction selection, stop/target change or management rescue occurred.

## Frozen variants

| Variant | Filled | Net R | Expectancy | 0.10-pip stress | Max DD | Net/DD | Bootstrap P(E>0) |
|---|---:|---:|---:|---:|---:|---:|---:|
| `MKT_NEXT_OPEN` | `630` | `-4.6398R` | `-0.00736R` | `-0.02691R` | `41.7964R` | `-0.1110` | `41.70%` |
| `LIMIT_ASIAN_BOUNDARY` | `555` | `-40.2782R` | `-0.07257R` | `-0.08266R` | `59.5425R` | `-0.6765` | `5.65%` |
| `LIMIT_HALF_RETRACE` | `591` | `-31.0868R` | `-0.05260R` | `-0.06159R` | `54.9637R` | `-0.5656` | `10.86%` |

All variants passed only the sample-size gates. Every effect, breadth, stability, drawdown, bootstrap and stress gate failed.

## Primary baseline — MKT_NEXT_OPEN

### Pooled

- attempted orders: `631`;
- filled trades: `630`;
- invalid geometry: `1`;
- net: `-4.6398R`;
- expectancy: `-0.00736R`;
- median trade: `-0.16584R`;
- win rate: `47.30%`;
- max drawdown: `41.7964R`;
- net/max-drawdown: `-0.1110`;
- median initial reward/risk: `1.2101`;
- `0.10` pip stress expectancy: `-0.02691R`;
- `0.25` pip stress expectancy: `-0.05623R`;
- calendar-week bootstrap 95% interval: `[-0.08564R, +0.06818R]`;
- bootstrap probability expectancy positive: `41.70%`.

### Pair attribution

| Pair | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| EURUSD | `323` | `+8.1640R` | `+0.02528R` |
| GBPUSD | `307` | `-12.8037R` | `-0.04171R` |

The contract prohibited an EURUSD-only rescue.

### Annual attribution

| Year | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| 2015 | `119` | `+1.7644R` | `+0.01483R` |
| 2016 | `138` | `-7.0847R` | `-0.05134R` |
| 2017 | `126` | `-11.1946R` | `-0.08885R` |
| 2018 | `126` | `-1.6559R` | `-0.01314R` |
| 2019 | `121` | `+13.5310R` | `+0.11183R` |

Only two of five years were positive.

### Exit anatomy

- stops: `285`, contributing exactly `-285R` before stress;
- targets: `234`, contributing approximately `+266.59R`;
- time exits: `111`, contributing approximately `+13.77R`.

The gross target and time-exit gains were almost sufficient to offset stops before additional stress, but not enough to produce a stable edge.

## Why prediction did not convert to executable expectancy

The predictive model remained directionally informative: higher score buckets reached the frozen midpoint outcome more often. However, higher scores were strongly associated with a deeper reclaim during the five-minute confirmation window.

By the time market entry became legal:

- a larger fraction of the reversal had already occurred;
- remaining distance to the midpoint target had contracted;
- entry-to-stop risk had not contracted proportionately;
- the reward/risk ratio deteriorated sharply;
- stop incidence remained substantial.

The market-entry probability quintiles demonstrate the conflict:

| Score quintile | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| Q1 | `124` | `+13.0682R` | `+0.10539R` |
| Q2 | `126` | `-8.2255R` | `-0.06528R` |
| Q3 | `125` | `+20.1088R` | `+0.16087R` |
| Q4 | `126` | `-5.9989R` | `-0.04761R` |
| Q5 | `129` | `-23.5924R` | `-0.18289R` |

The highest reversal-probability quintile was the worst executable quintile. This is not evidence that the model is inversely predictive. It shows that a probability model for midpoint completion is not an expectancy model when its strongest confirmation occurs after much of the available payoff has already been realised.

## Limit challengers

The two preregistered limit variants did not solve the timing/payoff problem:

- the Asian-boundary limit improved nominal entry reward/risk but filled a lower-quality subset and produced `-0.07257R` expectancy;
- the half-retrace limit produced `-0.05260R` expectancy;
- both pairs were negative for both variants;
- both variants were negative under all cost assumptions;
- neither met breadth, annual stability, drawdown or bootstrap gates.

No blended or retrospectively selected entry rule is permitted.

## Independent verification

A separate reconstruction reconciled the two pair artifacts with the pooled decision artifact and then checked every order against the original BID/ASK M1 files.

Confirmed:

- `1,910` order records exactly equal the two pair ledgers combined;
- `1,776` filled trades across the three variants;
- zero entries on or before the T5 timestamp;
- zero entries at or after 10:00 Amsterdam;
- zero inactive-quote entries;
- zero same-pair/date multiple fills per variant;
- zero market-entry price discrepancies;
- zero limit-fill or expiry discrepancies;
- zero unfilled orders that should have filled;
- zero stop/target/time-exit discrepancies;
- zero BID/ASK side discrepancies;
- zero base-R, `0.10` pip or `0.25` pip stress discrepancies;
- exact pair, year, drawdown and bootstrap reproduction.

No source, causality, fill, arithmetic or aggregation defect was found.

## Interpretation boundary

This decision rejects the specific executable formulation:

> wait for the complete T5 confirmation, enter afterward, target the Asian midpoint, and use the original `0.20 × range` adverse barrier.

It does not invalidate the predictive fingerprint programme. The model can still identify a higher probability of midpoint completion, but that information arrives too late to provide favorable reward/risk under the tested geometry.

A future reversal-execution programme would require a genuinely new causal hypothesis, such as an earlier staged T0–T5 decision process that enters before full confirmation and cancels on failed confirmation. That is not a parameter adjustment and must receive its own preregistration, branch, development evidence and untouched execution validation.

The separate continuation/fake-rejection programme also remains valid as a research candidate, but it must model continuation directly rather than invert this failed reversal strategy.

## Final disposition

- stop before 2020–2025 execution P&L;
- do not select EURUSD alone;
- do not remove losing years, weekdays or sweep directions;
- do not change the probability threshold;
- do not add partial exits, break-even rules, trailing stops or alternative target/stop grids;
- do not build Pine, alerts, paper trading or deployment for this formulation;
- preserve all evidence and convert the heavy workflow to manual reproduction only.
