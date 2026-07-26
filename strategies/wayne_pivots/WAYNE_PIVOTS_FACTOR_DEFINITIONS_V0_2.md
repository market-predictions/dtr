# Wayne Pivots — Exact Factor and Event Definitions v0.2

Date frozen: 2026-07-27

## Pivot day

Convert each UTC minute to `America/New_York`. The pivot day starts at 17:00 New York local time and ends immediately before the next 17:00 boundary. The day key is the UTC timestamp of the local 17:00 start.

A pivot day is valid when:

- both BID and ASK files are present;
- at least 1,200 active quote minutes exist;
- midpoint H/L/C are finite;
- prior valid pivot day exists;
- prior range is positive.

Pivots for day `d` use only H/L/C from completed day `d-1`.

## Midpoint and executable paths

Pivot levels use midpoint OHLC:

- midpoint open/close = average of BID and ASK open/close;
- midpoint high = average of BID high and ASK high;
- midpoint low = average of BID low and ASK low.

Anatomy first passage uses the midpoint minute path. Later execution uses ASK entry/BID exit for longs and BID entry/ASK exit for shorts.

## Traditional structure

For prior high `H`, low `L`, close `C`:

- `P = (H + L + C) / 3`
- `R1 = 2P - L`
- `S1 = 2P - H`
- `R2 = P + (H - L)`
- `S2 = P - (H - L)`
- `M1 = (S2 + S1) / 2`
- `M2 = (S1 + P) / 2`
- `M3 = (P + R1) / 2`
- `M4 = (R1 + R2) / 2`

## Direction families

### Unbiased anatomy

Evaluate both sides independently when their zone is touched:

- bull zone `[M2, P]`;
- bear zone `[P, M3]`.

### Book pivot-slope bias

Compare current P with previous pivot day's P:

- `BULL` when difference exceeds `+0.01 * prior_range`;
- `BEAR` when difference is below `-0.01 * prior_range`;
- `FLAT` otherwise.

The 1% prior-range tolerance is a numerical/noise guard and is not optimized.

## Zone-entry event

A zone is touched when the active midpoint minute range intersects the closed interval `[zone_low, zone_high]`.

The first touch of a zone in a pivot day is the only anatomy event for that side and structure. A day opening inside the zone is eligible and its first active minute is the event time.

Events are rejected when, before the first zone touch:

- the relevant invalidation level was already crossed; or
- the conservative target was already crossed.

These are labelled consumed structures rather than fresh entry opportunities.

## First-passage outcomes

Bull event:

- invalidation `S1`;
- targets `M4`, `R1`, `R2`.

Bear event:

- invalidation `R1`;
- targets `M1`, `S1`, `S2`.

Starting with the event minute, scan chronologically until the pivot-day boundary. For each target independently:

- target hit before invalidation = success;
- invalidation hit first = failure;
- both hit in the same unresolved minute = failure;
- neither hit before the boundary = censored failure for the strict target-before-invalidation measure.

Record MFE, MAE, elapsed minutes, target timestamp and invalidation timestamp.

## Path-value measure

For each event and target:

- entry anchor is the midpoint of the touched Wayne zone;
- risk is distance from anchor to invalidation;
- reward is distance from anchor to target;
- strict payoff proxy is `reward/risk` on success and `-1R` otherwise.

This is an anatomy proxy, not executable strategy P&L.

## Placebo structures

All placebos preserve every distance from the Wayne P. Only the central anchor changes. For placebo anchor `A`, every level is translated by `A - P`.

Frozen anchors:

1. prior close `C`;
2. prior range midpoint `(H + L) / 2`;
3. lower quartile `L + 0.25(H-L)`;
4. upper quartile `L + 0.75(H-L)`;
5. Wayne structure shifted down `0.25(H-L)`;
6. Wayne structure shifted up `0.25(H-L)`;
7. synthetic anchor S1: `0.02493530H + 0.46716300L + 0.50790170C`;
8. synthetic anchor S2: `0.50115999H + 0.08985396L + 0.40898605C`;
9. synthetic anchor S3: `0.20219939H + 0.21936514L + 0.57843547C`;
10. synthetic anchor S4: `0.58049413H + 0.36543086L + 0.05407500C`.

Synthetic weights were generated once from NumPy default RNG seed `20260727` and are now frozen.

## Primary comparison

For each pair-day, side and target, compare the Wayne event with each matched placebo structure on the same underlying price path. Report:

- eligible event count;
- success rate;
- mean strict payoff proxy;
- Wayne-minus-placebo success lift;
- Wayne-minus-placebo payoff effect;
- pair/year attribution;
- date-block bootstrap;
- false-discovery-rate correction across the complete comparison family.

No placebo is removed after outcome inspection.

## Primary years and source isolation

The first authoritative anatomy run may access only annual source partitions 2015–2021. Source files for 2022 onward must not enter the job directory.

## Gate boundary

No H4/M15 technical bias, macro bias, execution arm, role-reversal setup, weekly pivot, monthly pivot or developing future-pivot outcome may be opened until the daily Wayne geometry beats matched placebos under the preregistered gate.
