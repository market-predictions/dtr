# Quarters Theory Stage-1 Preregistration

**Version:** 0.3.0  
**Date:** 2026-08-05  
**Primary pair:** GBP/USD  
**Development data:** 2015-2019  
**Internal validation:** 2020-2021  
**Reserved holdout:** 2022-2025

## Primary hypothesis

Canonical Large Quarter Points, defined as price levels whose pip index is congruent to zero modulo 250, produce greater directionally aligned 60-minute continuation after crossing than other 50-pip round levels of matched 100-pip roundness.

## Null hypothesis

After conditioning on year, crossing direction, whole-versus-half 100-pip class and four-hour UTC session, canonical LQP crossings do not outperform non-LQP 50-pip round-level crossings.

## Primary endpoint

Directional midpoint return in pips from the crossing-minute close to 60 minutes after crossing.

## Primary event rule

- Candidate levels occur every 50 pips.
- Crossing requires consecutive active bid and ask minutes.
- Bullish crossing: prior midpoint close below level and current close at or above level.
- Bearish crossing: prior midpoint close above level and current close at or below level.
- A level-direction pair rearms only after midpoint price returns at least 25 pips to the origin side.
- The primary study does not globally suppress adjacent-level events; dependence is handled through calendar-week block inference.
- A horizon is valid when at least 80% of its future calendar minutes contain active bid and ask quotes.

## Matching and estimation

Primary strata are year, direction, whole-100 versus half-100 roundness and four-hour UTC session. Within each supported stratum, calculate the canonical mean minus the pooled non-canonical mean. Aggregate using the harmonic treated/control sample-size weight.

Uncertainty is estimated by resampling calendar weeks with replacement **within each year**. This preserves the historical year mix and serial dependence inside each week.

## Secondary endpoints

- directional returns at 5, 15, 30, 120, 240 and 1,440 minutes;
- 60-minute MFE and MAE;
- first passage to +10 versus -10 pips within 60 minutes;
- canonical phase rank among the five 250-pip phases;
- week-clustered covariate-adjusted regressions.

## Prespecified sensitivities

- reset distances of 15, 25 and 50 pips;
- entry crossing overshoot caps of 3, 5 and 10 pips;
- maximum crossing spread of 3 pips;
- development versus internal-validation sign consistency.

## Interpretation gate

Stage 1 supports continuation only when the canonical effect is positive, stable in sign between development and validation, not dependent on one event-quality rule, and large enough to remain economically relevant after realistic execution costs.

A null or negative result blocks strategy optimization. It does not prove that every broader discretionary implementation of Yotov's methodology is invalid.

## Holdout governance

The 2022-2025 file name, manifest and first rows were inspected only to establish schema and date range before the correct development archive was located. No level-event extraction, endpoint calculation, strategy test or performance comparison was run on 2022-2025. It remains outcome-unopened and must not be opened without a new registered decision.
