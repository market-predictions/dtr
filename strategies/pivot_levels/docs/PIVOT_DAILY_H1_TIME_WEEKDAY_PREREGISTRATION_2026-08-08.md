# Preregistration — Daily S1/R1 × H1 Rejection: Time-of-Day and Weekday Heterogeneity

Date: 2026-08-08
Study ID: `DFXC-20260808-007-pivot-daily-time-weekday`
Parent studies: `DFXC-20260808-003-pivot-daily-wick-holdout`, `DFXC-20260808-006-pivot-daily-level-decomposition`
Dataset: **Dukascopy FX Cash**
Study type: causal/forward heterogeneity study on previously exposed data
Status: `FROZEN_PRE_OUTCOME`

## Research question

Does the observable Daily S1/R1 + strong directional H1 rejection signal have materially different forward reversal behavior depending on major FX session phase and day of week?

The purpose is to test **time as an independent conditioning variable**. Time is not yet a trading filter. The study must distinguish:

- session start / Hour 1;
- Hour 2;
- Hour 3;
- time outside those three-hour transition windows;
- weekday Monday through Friday under the NY17 FX trading-date calendar.

## Parent signal — frozen

Classic daily floor pivots from the prior completed NY17 FX trading day:

- `PP = (H + L + C) / 3`
- `R1 = 2*PP - L`
- `S1 = 2*PP - H`
- `R2 = PP + (H-L)`
- `S2 = PP - (H-L)`
- `R3 = H + 2*(PP-L)`
- `S3 = L - 2*(H-PP)`

For each H1 high/low observation, assign the nearest pivot using the parent side-specific adjacent-level spacing. Normalized distance is `d = abs(extreme-pivot)/local_spacing`.

Primary price tier:

- first-order pivots = `S1` or `R1`;
- signal core = `0 <= d < 0.20`;
- strong directional rejection wick = wick fraction `>= 0.30`;
- high-side signal direction = short/reversal-down;
- low-side signal direction = long/reversal-up.

Controls:

1. same strong-wick signal at `S2/R2` under identical geometry;
2. strong directional wick in the matched parent outer band `0.30 <= d <= 0.50` around S1/R1;
3. all non-transition hours as time control.

No level, wick-threshold, zone-width, pair or session selection may be changed after outcomes.

## Observable timing and entry reference

The signal is observable only at the H1 candle close. Forward measurement begins from the **next active H1 open** after the signal candle. No terminal/extremum hindsight label is required for the primary forward endpoints.

If both high-side and low-side qualifying signals occur on the same H1 candle, retain both as separate structural signal observations and report their frequency; do not silently choose one side.

## Session anchors — DST-safe and frozen

Session hours are defined in local market time, then mapped to UTC using the applicable IANA timezone for each timestamp.

### Tokyo

Session anchor: **09:00 Asia/Tokyo**.

- `TOKYO_H1`: 09:00–09:59 JST
- `TOKYO_H2`: 10:00–10:59 JST
- `TOKYO_H3`: 11:00–11:59 JST

### London

Session anchor: **08:00 Europe/London**.

- `LONDON_H1`: 08:00–08:59 London local time
- `LONDON_H2`: 09:00–09:59
- `LONDON_H3`: 10:00–10:59

### New York FX

Session anchor: **08:00 America/New_York**.

- `NEWYORK_H1`: 08:00–08:59 ET
- `NEWYORK_H2`: 09:00–09:59
- `NEWYORK_H3`: 10:00–10:59

All other H1 bars are `NON_TRANSITION` for the primary session-phase comparison.

The three-hour design is intentional. Hour 1 tests the opening liquidity impulse, Hour 2 tests immediate post-open digestion/continuation/reversal, and Hour 3 tests whether any effect persists rather than being confined to the first two hours.

## Full 24-hour profile

A UTC 0–23 hour profile is produced descriptively to visualize the shape of the effect. It is **not** a 24-way strategy-selection family. No single UTC hour may be promoted solely because it is the maximum observed hour.

## Weekday

Weekday is derived from the existing NY17 FX trading date, not the UTC calendar date.

Frozen categories:

- Monday
- Tuesday
- Wednesday
- Thursday
- Friday

Weekend labels are invalid for eligible FX trading dates and indicate an implementation defect.

## Data partitions

All existing 2015–2025 history is scientifically exposed by related pivot research, so this study does not claim a pristine holdout.

For stability assessment only:

- development: 2015–2019;
- internal validation: 2020–2021;
- related-sample replication: 2022–2025.

2026 remains unused for outcome research in this study.

## Forward endpoints

All returns are direction-adjusted so positive means movement in the reversal direction indicated by the wick.

ATR reference: lagged H1 ATR24 available at signal close.

### Primary endpoint

`FWD4_ATR_RETURN` = direction-adjusted next-active-H1-open to close four active H1 bars later, divided by signal ATR24.

### Secondary endpoints

- `FWD1_ATR_RETURN`
- `FWD2_ATR_RETURN`
- `FWD8_ATR_RETURN`
- 4H maximum favorable excursion (`MFE4_ATR`)
- 4H maximum adverse excursion (`MAE4_ATR`)
- `MFE4_ATR - MAE4_ATR`
- probability `FWD4_ATR_RETURN > 0`

These endpoints are descriptive companions and may not replace the primary endpoint after inspection.

## Primary time hypotheses

For S1/R1 strong-wick core signals, estimate the difference in mean `FWD4_ATR_RETURN` between each of the nine session-phase buckets and `NON_TRANSITION`:

1. TOKYO_H1
2. TOKYO_H2
3. TOKYO_H3
4. LONDON_H1
5. LONDON_H2
6. LONDON_H3
7. NEWYORK_H1
8. NEWYORK_H2
9. NEWYORK_H3

Inference family: nine comparisons with Holm correction.

For every phase, also report the **first-order specificity contrast**:

`[S1/R1 phase - S1/R1 non-transition] - [S2/R2 phase - S2/R2 non-transition]`

This tests whether a session effect is genuinely stronger at first-order pivots rather than generic session-time wick behavior.

## Weekday hypothesis

Weekday is initially an omnibus heterogeneity diagnostic, not a best-day selection problem.

Report S1/R1 mean `FWD4_ATR_RETURN` and secondary endpoints for Monday–Friday. A pair-year clustered bootstrap is used to estimate pairwise weekday intervals, but no weekday is promoted unless:

- the pattern is directionally stable across development, validation and related-sample replication; and
- any later weekday-selection study is separately preregistered on fresh evidence.

## Inference

- cluster unit: pair-year;
- 5,000 clustered bootstrap draws for primary phase effects and confidence intervals;
- Holm correction across the nine session-phase versus non-transition primary comparisons;
- pair breadth, calendar-year breadth and partition stability reported for any apparently strong phase;
- no pair removal or session-window adjustment after inspection.

## Decision rules

This study can support one of the following broad conclusions:

- `TIME_HETEROGENEITY_SUPPORTED_SESSION_PHASE_MATTERS`
- `TIME_HETEROGENEITY_WEAK_OR_INCONSISTENT`
- `NO_MATERIAL_TIME_HETEROGENEITY`
- `INDETERMINATE_IMPLEMENTATION_OR_SAMPLE_LIMITATION`

A positive time result does not create a live entry rule. Any selected session/hour/day filter requires a separately preregistered execution-confirmation study on genuinely fresh data or an independent qualified dataset.

## Prohibited rescue

After time outcomes are inspected, do not:

- redefine the session opens;
- add a fourth/fifth session hour because it looks better;
- shift London/New York opens by 30 or 60 minutes;
- select arbitrary clock windows;
- drop pairs or weekdays;
- change S1/R1 to another level family;
- change the 20% core or 30% wick threshold;
- change the primary 4H horizon;
- use the descriptive 24-hour maximum as a trading filter.
