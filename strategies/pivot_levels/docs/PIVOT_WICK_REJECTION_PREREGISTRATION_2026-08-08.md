# Pivot-Zone Wick Rejection Study — Conditional Preregistration

Date: 2026-08-08
Programme: `PIVOT-WICK-REJECTION-V1`
Study ID: `DFXC-20260808-002-pivot-wick-rejection`
Status at creation: `FROZEN_PRE_OUTCOME_CONDITIONAL`
Parent: `DFXC-20260808-001-pivot-multiscale-terminal`

## Research question

Among pivot-horizon / directional-leg mappings that survive the frozen multiscale terminal-zone study, does directionally appropriate wick rejection inside the pivot core add observable predictive information about independently defined leg termination beyond (a) pivot proximity and (b) generic wick behaviour away from pivots?

The terminal label remains pivot-blind and wick-blind. Wicks are candidate predictors measured at candle close, never part of the terminal definition.

## Conditional eligibility

This study runs only for mappings that pass **all** promotion gates in `PIVOT-MULTISCALE-TERMINAL-ZONE-V1`.

The eligibility rule is frozen before multiscale outcomes. If no mapping survives, this study stops without testing alternative mappings or weakening the parent gate.

## Data and geometry

- Same Dukascopy FX Cash pair universe, midpoint construction and 2015-2021 exposed research sample as the parent.
- Protected 2022-2025 remains unopened.
- Same classic pivots, named levels/midlevels, normalized spacing geometry and scale-aligned detector timeframe as the parent.
- Pivot core: normalized distance `0-20%`.
- Outer comparison region: `30-50%`.

## Directional wick definition

For every eligible detector candle with positive total range `R = H-L`:

- high-side rejection wick fraction: `(H - max(O,C)) / R`;
- low-side rejection wick fraction: `(min(O,C) - L) / R`.

The high-side fraction is paired only with high-side terminal observations; the low-side fraction only with low-side observations. Zero-range candles are excluded.

This metric is known at detector-candle close and therefore is observable before the later ATR directional-change confirmation that supplies the terminal label.

## Primary strong/weak definition

Frozen absolute bins of directional wick fraction:

- weak: `< 10%` of candle range;
- intermediate-low: `10-20%`;
- intermediate-high: `20-30%`;
- strong: `30-40%`;
- very strong: `>= 40%`.

The primary strong-rejection group is `>=30%`; the primary weak group is `<10%`. Intermediate observations remain in descriptive gradient outputs but are not used in the primary 2x2 contrast.

## Primary interaction endpoint

For each eligible parent mapping calculate:

`[(terminal_rate_core_strong - terminal_rate_core_weak) - (terminal_rate_outer_strong - terminal_rate_outer_weak)]`

This difference-in-differences asks whether a strong directional wick is **more informative near a pivot core** than the generic exhaustion information contained in the same wick geometry away from pivots.

Required companion effects:

1. generic wick effect in the outer region;
2. pivot-core effect among weak-wick observations;
3. pivot-core strong-wick terminal rate;
4. five-bin wick-strength gradient separately in core and outer regions.

## Secondary observable rejection variables

These are robustness/descriptive variables only and cannot rescue a failed primary interaction:

- close rejection fraction: high side `(H-C)/R`, low side `(C-L)/R`;
- directional wick dominance: directional wick divided by total upper+lower wick when denominator is positive;
- close-back/reclaim flag: candle extreme enters the 0-20% pivot core while the close finishes farther from the pivot than the extreme.

No composite score weights may be optimized in this study.

## Inference

- Same development 2015-2019 and internal validation 2020-2021 split.
- Cluster bootstrap unit: pair-year.
- 5,000 draws.
- Holm correction across all eligible parent mappings, with a maximum family size of five.
- Pair breadth and leave-one-pair-out checks are mandatory.

Because eligibility is selected on the same 2015-2021 sample by the parent structural study, a passing wick interaction is classified as a **conditional internal mechanism result**, not independent confirmation.

## Internal mechanism gate

A mapping's wick interaction qualifies for future independent confirmation only if:

1. development and validation interaction effects are both positive;
2. combined 95% interval is strictly above zero;
3. Holm-adjusted two-sided p < 0.05;
4. at least 6/10 eligible pairs show positive interaction;
5. every leave-one-pair-out pooled interaction remains positive;
6. core terminal incidence rises directionally across the five frozen wick-strength bins;
7. the effect is not explained solely by generic strong-wick exhaustion in the outer region.

## Interpretation boundary

A positive result would establish that wick rejection is an observable exhaustion signature that interacts with pivot proximity. It would still not establish an executable reversal entry, because actual confirmation, stop placement, lower-timeframe trigger design and transaction costs remain untested.

## Restrictions

- No 2022-2025 holdout opening.
- No wick-threshold tuning after outcomes.
- No replacement of the independent ATR terminal definition with wick-defined termination.
- No pair/session/year/level shopping.
- No volume or tick-activity filters in this phase.
- No P&L, Pine, alerts, sizing, paper trading or deployment.
- If the interaction fails, do not rescue it with secondary close/reclaim variables or a post-hoc composite score.
