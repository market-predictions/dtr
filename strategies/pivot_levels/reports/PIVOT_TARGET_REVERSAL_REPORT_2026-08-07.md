# Pivot Levels as Targets, Stall Zones and Reversal Zones

**Programme:** `PIVOT-TARGET-REVERSAL-V1`  
**Date:** 2026-08-07  
**Data:** registered Dukascopy FX Cache, ten FX pairs, 2015–2021  
**Binding decision:** `NO_PIVOT_MECHANISM_PASSES_INTERNAL_GATE`  
**Independent assurance:** `PASS`

## Executive conclusion

Classic floor pivots produce a remarkably stable **absolute reach ladder**: PP is reached fresh in roughly four out of five active periods; R1/S1 in roughly 41–47%; R2/S2 in roughly 15–19%; and R3/S3 only in the mid-single digits. For monthly and quarterly pivots, the inner midlevels between PP and R1/S1 are reached in roughly 72–74% of active periods.

However, none of the 20 preregistered pivot-specific mechanisms survives the internal gate when each exact pivot coordinate is compared with nearby deterministic non-pivot placebo coordinates. The data therefore support pivots as a **probabilistic distance/range map**, but do not establish the exact pivot coordinate as a privileged magnet, stall point or reversal point.

The 2022–2025 holdout remains unopened.

## Study design

- Classic floor pivots from the immediately completed prior period.
- Daily and weekly: S3/S2/S1/PP/R1/R2/R3.
- Monthly, quarterly and yearly: those seven levels plus all six adjacent arithmetic midlevels.
- FX daily boundary: 17:00 America/New_York, DST-safe.
- Structural trend layer: H1; first-passage/reaction layer: deterministic M15 derived from the verified M1 source.
- Pivot tolerance half-zone: `min(25 pips, 0.10 × prior ATR20_D1, 0.10 × local spacing)`.
- Nearby placebos: exact pivot ±25% of local pivot spacing.
- Development: 2015–2019; internal validation: 2020–2021.
- 5,000 pair-year-week clustered bootstrap draws and Holm correction over 20 primary hypotheses.

P0 measures fresh touch probability. P1 tests independent trend-leg endpoint clustering. P2 tests trend-approach target completion. P3 explicitly permits sideways rotation inside the tolerance zone and tests containment/stall before meaningful continuation. P4 tests whether the eventual meaningful exit is reversal-first rather than continuation-first; time inside the zone is neutral.

## Absolute target likelihood — fresh touch census

These are **absolute** observed fresh-touch rates, not evidence that the exact pivot coordinate itself causes the move.

### Daily and weekly

| Timeframe | PP | R1 | S1 | R2 | S2 | R3 | S3 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Daily | 79.3% | 47.0% | 46.5% | 18.5% | 18.8% | 6.4% | 7.2% |
| Weekly | 79.3% | 46.9% | 46.0% | 17.5% | 18.0% | 5.9% | 5.9% |

### Monthly and quarterly, including midlevels

| Timeframe | PP | PP–R1 mid | S1–PP mid | R1 | S1 | R1–R2 mid | S2–S1 mid | R2 | S2 | R2–R3 mid | S3–S2 mid | R3 | S3 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Monthly | 82.2% | 71.3% | 71.8% | 44.5% | 43.7% | 25.2% | 28.4% | 16.3% | 18.2% | 9.0% | 11.3% | 4.7% | 6.1% |
| Quarterly | 81.0% | 73.6% | 71.9% | 41.1% | 45.2% | 23.7% | 27.4% | 15.6% | 17.4% | 9.3% | 10.0% | 4.1% | 3.7% |

### Yearly — descriptive only

Yearly has only about 60 pair-year observations across active 2016–2021 periods and is visibly noisier: PP 78.0%, PP–R1 mid 70.0%, S1–PP mid 75.0%, R1 30.0%, S1 46.7%, R2 10.0%, S2 16.7%, R3 5.0%, S3 10.0%.

## Pivot-specific mechanism results versus nearby controls

Effects below are real-pivot minus nearby-placebo probability/score differences. Positive favors the exact pivot coordinate.

| Timeframe | P1 endpoint clustering | P2 target completion | P3 containment/stall | P4 reversal-first |
|---|---:|---:|---:|---:|
| Daily | −0.04 pp [−0.07, −0.01] | +0.81 pp [−1.17, +2.87] | +2.57 pp [−1.06, +5.91] | +0.09 pp [−2.67, +2.53] |
| Weekly | −0.03 pp [−0.05, −0.00] | +0.21 pp [−4.52, +5.23] | +2.81 pp [−5.75, +12.61] | −2.03 pp [−6.93, +3.09] |
| Monthly | −0.00 pp [−0.02, +0.01] | +3.34 pp [−3.46, +9.75] | +2.35 pp [−10.03, +14.61] | +1.06 pp [−5.64, +7.90] |
| Quarterly | +0.00 pp [−0.02, +0.02] | +0.33 pp [−9.56, +10.06] | −5.66 pp [−27.18, +12.09] | −1.42 pp [−12.24, +10.30] |
| Yearly | +0.02 pp [−0.01, +0.04] | −4.23 pp [−19.12, +11.90] | −1.20 pp [−27.72, +24.49] | −15.66 pp [−39.95, +4.71] |

Daily endpoint clustering is slightly negative and its unadjusted interval is below zero, but its Holm-adjusted p-value is 0.096, so it does not pass the frozen 20-test familywise gate. Weekly endpoint clustering is also slightly negative. Weekly containment is descriptively +2.81 pp with 8/10 pair effects positive, but its interval is very wide. Monthly target completion is the strongest positive descriptive candidate at +3.34 pp and is positive in both development and validation, but its interval crosses zero and only 4/10 pair effects are positive. No quarterly or yearly mechanism qualifies.

## Reversal likelihood caveat

Conditional raw reversal-first rates after a qualified trend reaches a real pivot zone are often roughly 85–95% in this barrier geometry. **That is not a pivot edge.** Nearby placebo coordinates show similarly high reversal-first rates. The preregistered decision metric is the matched real-minus-placebo difference, and those differences are approximately zero across all timeframes.

The evidence therefore supports a generic arrival/exhaustion phenomenon under this barrier definition, not privileged classic-pivot reversal geometry.

## Integrity and assurance

- P0 census rows: 166,434.
- P1 endpoint comparisons: 1,304,522.
- P2–P4 approach/reaction events: 92,470.
- Independent source assurance rehashed 140 compressed annual side-files: ten pairs × seven years × BID/ASK.
- Pivot formulas, all requested midlevels and the New York 17:00 DST boundary were independently recomputed.
- A separate 2,000-draw pair-year-week bootstrap with seed 99170807 reproduced every primary point estimate exactly and again produced no qualifying positive confidence interval.
- No analysis ledger contains a year after 2021.

Independent assurance decision: `PASS`.

## Binding decision

`NO_PIVOT_MECHANISM_PASSES_INTERNAL_GATE`

No primary timeframe/mechanism combination satisfies all frozen conditions: positive development and validation, combined 95% interval above zero, Holm-adjusted p<0.05, at least 6/10 positive pairs, positive leave-one-pair-out effects, and no dominant pair/level.

The study does **not** justify opening the 2022–2025 holdout, tuning formulas or tolerance widths, selecting favorable pairs, or constructing a pivot strategy from the apparent weekly/monthly descriptive effects.

The useful result is narrower: classic pivots can be retained as a **descriptive probabilistic reach ladder**. The current evidence does not justify saying that price is attracted to, stalls at, or reverses from the *exact classic pivot coordinate* more than it would at a nearby non-pivot coordinate.

## Limitations

- M15 first-passage resolution conservatively classifies same-bar target/failure or reversal/extension as ambiguous/non-success.
- Pivot specificity is tested against nearby local placebos, not every conceivable range-normalized coordinate.
- Yearly pivots have low sample size in a seven-year research window.
- This is price-only research; no volume-at-price, order-flow, dealer inventory or options positioning is present in the Dukascopy M1 cache.

## Authorization boundary

Not authorized from this study: 2022–2025 holdout opening, formula/parameter rescue, execution P&L, entry/stop/target optimization, Pine, alerts, sizing, paper trading or deployment.