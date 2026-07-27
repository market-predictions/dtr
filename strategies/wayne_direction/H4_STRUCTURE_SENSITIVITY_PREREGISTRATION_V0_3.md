# Wayne Direction-First H4 Structural Sensitivity — Preregistration v0.3

Date: 2026-07-27

## Reason for this stage

The frozen D1 sequence produced 83 complete trend transitions across six pairs and seven years. It was temporally broad and aligned with healthy H4 averages at 83.13% of confirmation bars, but its state persisted too slowly to represent current technical direction at later monthly opens.

The D1 contract remains unchanged and retained as strategic regime context. This stage tests whether the exact same dimensionless structure sequence on completed H4 bars is a more appropriate current technical-direction layer.

## No-retuning rule

The H4 study applies the existing `TrendConfig` unchanged in H4-bar units:

- two-bar left and right swing confirmation;
- ATR20 volatility scale;
- 0.20 ATR double-bottom/top tolerance;
- 0.05 ATR break buffer;
- ±0.15 ATR retest band;
- 5–60 H4-bar separation between the double extremes;
- maximum 30 H4 bars from double extreme to BOS;
- maximum 20 H4 bars from BOS to retest;
- maximum 30 H4 bars from higher low/lower high to continuation confirmation.

No parameter grid, time-horizon rescaling or post-hoc threshold change is authorized.

## Causal source

- six primary FX pairs;
- qualified M1 BID/ASK source;
- development years 2015–2021 only;
- New York 17:00 pivot day;
- six local-wall-clock H4 bars per pivot day;
- DST transitions preserved as 3-hour or 5-hour elapsed H4 buckets where necessary;
- structure and EMA health sampled only after the H4 bar closes.

## H4 direction sequence

Bullish:

1. double bottom;
2. completed H4 close above the intervening neckline plus 0.05 ATR;
3. retest of the neckline band;
4. causally confirmed higher low;
5. completed H4 close above the pre-retest impulse high plus 0.05 ATR.

Bearish rules are mirrored.

The H4 direction is `NONE` until step 5. BOS alone is not direction.

## H4 health

At the same completed H4 timestamp:

- bullish healthy: EMA21 > EMA55 > EMA200 and state is `BULL_EXPANDING` or `BULL_STABLE`;
- bearish healthy: EMA21 < EMA55 < EMA200 and state is `BEAR_EXPANDING` or `BEAR_STABLE`;
- compressed, mixed and conflicted states are not healthy.

## D1 relationship

The D1 strategic state is attached but does not create the H4 signal.

Fixed D1 relationship categories:

- `D1_ALIGNED`;
- `D1_NONE`;
- `D1_OPPOSED`.

No two-factor optimization is permitted. These categories are attribution diagnostics.

## Month-open attribution

At each FX trading month open, sample:

- last completed H4 structural direction;
- last completed H4 health state;
- last completed D1 strategic direction;
- prior-month traditional pivot levels;
- current month open location.

Bullish monthly location is M2–P. Bearish monthly location is P–M3.

Fixed H4 relationship categories for a zone side:

1. `ALIGNED_HEALTHY` — H4 structure agrees and H4 averages are stable/expanding in that direction;
2. `ALIGNED_UNHEALTHY` — H4 structure agrees but H4 health is compressed, mixed or conflicted;
3. `NO_H4_DIRECTION` — H4 structure is neutral;
4. `OPPOSITE_H4_DIRECTION` — H4 structure opposes the zone side.

## Outcomes

Descriptive month-end reach only:

- bullish zone: M4 and R2;
- bearish zone: M1 and S2.

A target is reached when the current month's high/low first crosses the level before month-end. This stage does not model entry price, stop, intraday structural invalidation, transaction costs or P&L.

## Sample-sufficiency gates

### H4 transition census

Pass only if:

- at least 300 pooled complete H4 trend confirmations;
- at least 40 confirmations in four or more pairs.

### Fully aligned monthly opportunity census

Pass only if:

- at least 80 unique `ALIGNED_HEALTHY` direction-plus-zone months pooled;
- at least 10 such months in four or more pairs.

These gates authorize statistical attribution only. They do not establish an edge.

## Required outputs

- pair-level H4 transition census;
- bullish/bearish event funnel;
- H4 health at confirmation;
- H4 run-duration distribution;
- month-open category census;
- month-end reach by H4 category, D1 relationship, pair and year;
- decision on whether the trend layer has adequate sample for regime, seasonality and macro attribution.

## Protected boundaries

- D1 thresholds remain frozen;
- H4 thresholds are not tuned;
- daily pivots remain excluded;
- no pair, year, side or category is discarded;
- no macro, regime or seasonality outcome is opened in this stage;
- no entry, stop, partial exit, runner, breakeven, Pine or deployment work is authorized.
