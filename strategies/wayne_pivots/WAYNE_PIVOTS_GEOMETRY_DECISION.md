# Wayne McDonell Daily Pivot Geometry — Final Decision

Date: 2026-07-27  
Decision: `FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS`

## Authoritative evidence

- GitHub Actions run: `30223457477`;
- evaluated scientific head: `1261ff8b30795c3eda7218b74e605123b11c0cee`;
- decision artifact: `wayne-pivots-daily-geometry-decision`;
- artifact digest: `sha256:6272c9ee5a71ff7d070f718e3ff56620c9615ca7380bb1343182e7751d2f1556`;
- general repository lint and Python 3.11/3.12 tests: success;
- frozen Wayne contract tests and lint: success;
- all six source-restoration, 2015–2021 isolation and pair-ledger jobs: success;
- pooled geometry, bootstrap, permutation and FDR calculations: success;
- the workflow failed only at the deliberate bias-authorization step.

## Population

- pairs: AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- years: 2015–2021 only;
- New York 17:00 pivot-day boundary;
- 596,277 event-target rows;
- 547,764 fresh event-target rows;
- zero duplicate instrument/day/structure/side/target keys;
- 11 structures: Wayne plus ten frozen placebos;
- 60 Wayne-versus-placebo comparisons.

No source or event row from 2022 onward entered the scientific artifact.

## Source-faithful Wayne anatomy

| Side and target | Fresh Wayne events | Success rate | Mean strict payoff proxy |
|---|---:|---:|---:|
| Bull to M4 | 9,241 | 17.45% | -0.4135R |
| Bull to R1 | 9,241 | 29.91% | -0.2052R |
| Bull to R2 | 9,241 | 10.56% | -0.5711R |
| Bear to M1 | 9,382 | 18.35% | -0.3816R |
| Bear to S1 | 9,382 | 29.75% | -0.2087R |
| Bear to S2 | 9,382 | 11.24% | -0.5430R |

The strict payoff value is a causal anatomy proxy based on the frozen zone midpoint, target and invalidation. It is not executable strategy P&L.

Every side/target payoff was negative in every one of the six pairs. Every annual mean was also negative from 2015 through 2021.

## Candidate decisions

| Candidate | Positive success comparisons | Positive payoff comparisons | Full comparison passes | Core-anchor pass | Geometry decision |
|---|---:|---:|---:|---|---|
| Bull to M4 | 5 of 10 | 5 of 10 | 4 | No | Fail |
| Bull to R1 | 5 of 10 | 5 of 10 | 4 | No | Fail |
| Bull to R2 | 5 of 10 | 5 of 10 | 3 | No | Fail |
| Bear to M1 | 5 of 10 | 5 of 10 | 3 | No | Fail |
| Bear to S1 | 4 of 10 | 4 of 10 | 3 | No | Fail |
| Bear to S2 | 5 of 10 | 5 of 10 | 3 | No | Fail |

Twenty individual comparisons passed their complete statistical gates, but no source-faithful candidate passed the family-level geometry gate.

## Why some placebo comparisons passed

Wayne's anchor lies near the central portion of the prior range. Consequently:

- bullish Wayne zones strongly outperformed structures translated upward, but strongly underperformed structures translated downward;
- bearish Wayne zones strongly outperformed structures translated downward, but strongly underperformed structures translated upward.

Examples:

- bull to R1 versus `SHIFT_UP_025`: +19.75 percentage-point hit lift and +0.5450R payoff effect;
- bull to R1 versus `SHIFT_DOWN_025`: -20.52 percentage-point hit lift and -0.5071R payoff effect;
- bear to S1 versus `SHIFT_DOWN_025`: +19.07 percentage-point hit lift and +0.5258R payoff effect;
- bear to S1 versus `SHIFT_UP_025`: -20.68 percentage-point hit lift and -0.5082R payoff effect.

This mirror symmetry shows that relative location within the prior range matters. It does not show that the Wayne anchor `(H + L + C) / 3` is uniquely informative.

## Core-anchor comparison

The serious uniqueness controls were the prior close and the prior-range midpoint.

### Versus prior close

Wayne was worse in five of six side/target comparisons:

| Candidate | Success lift | Payoff effect |
|---|---:|---:|
| Bull to M4 | -2.05 pp | -0.0276R |
| Bull to R1 | -4.82 pp | -0.0555R |
| Bull to R2 | -0.56 pp | +0.0005R |
| Bear to M1 | -1.61 pp | -0.0122R |
| Bear to S1 | -5.51 pp | -0.0733R |
| Bear to S2 | -0.93 pp | -0.0141R |

The sole positive payoff difference, bull to R2, was economically negligible and had no supporting statistical evidence.

### Versus prior-range midpoint

Wayne was close to the range midpoint:

| Candidate | Success lift | Payoff effect |
|---|---:|---:|
| Bull to M4 | +0.63 pp | +0.0035R |
| Bull to R1 | +2.59 pp | +0.0392R |
| Bull to R2 | +0.27 pp | -0.0000R |
| Bear to M1 | +0.63 pp | +0.0033R |
| Bear to S1 | +2.60 pp | +0.0400R |
| Bear to S2 | +0.45 pp | +0.0085R |

R1/S1 differences were broad and statistically detectable, but the hit-rate lift remained only about +2.6 percentage points, below the frozen +5-point uniqueness threshold. No prior-close or range-midpoint comparison passed the complete individual gate.

## Interpretation

The study supports three conclusions:

1. prior-range location has strong effects on target-before-invalidation paths;
2. arbitrary displacement can make a pivot structure materially better or worse;
3. the traditional Wayne central anchor did not outperform robust generic anchors sufficiently to establish unique pivot geometry.

The result does not prove that every Wayne-style discretionary system is invalid. McDonell's complete methodology also uses directional bias, market speed, trend, momentum, announcements and abstention. It does establish that the daily traditional pivot formula did not earn independent credit before those layers were introduced.

Opening directional bias now would violate the preregistered research hierarchy and would make it impossible to distinguish pivot value from bias value. A future study of the complete decision system would therefore need a new preregistration and must compare the same bias and trigger with Wayne zones versus generic prior-close and range-midpoint zones.

## Binding consequences

- no pivot-slope, H4/M15 technical, macro or fundamental-bias outcome is opened in this programme;
- no six-arm execution study is opened;
- no role-reversal, weekly, monthly or developing future-pivot research is opened;
- no 2022–2025 data is inspected by this work package;
- no pair, year, side, target, period-boundary or placebo rescue is permitted;
- no Pine, alerts, sizing, paper trading or deployment is authorized.

## Programme conclusion

`FAIL_DAILY_PIVOT_GEOMETRY_STOP_BEFORE_BIAS`

The daily Wayne pivot structure behaves like one central prior-range geometry among several plausible alternatives. It is materially superior to some displaced anchors and materially inferior to others, while failing to beat the prior close and range midpoint under the frozen uniqueness standard. The current incremental-pivot-value path is closed before directional bias and execution.
