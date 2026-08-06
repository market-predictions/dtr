# Structural Trend State Machine v0.1

Date: 2026-07-27

## Purpose

Translate the user-defined market-structure sequence into a deterministic, causal state machine:

> double bottom → higher-high break of structure → retest → higher low → higher high.

The bearish sequence is the exact mirror.

## Timeframe

Primary structure timeframe: completed New York 17:00 D1 bars.

H4 bars do not create the structural direction. They grade the health of a direction already confirmed on D1.

## Confirmed swing points

A swing high or swing low is confirmed with a two-bar right-side delay:

- swing low at bar `t`: low[t] is strictly lower than lows at t-2, t-1, t+1 and t+2;
- swing high at bar `t`: high[t] is strictly higher than highs at t-2, t-1, t+1 and t+2.

The swing becomes observable only after bar `t+2` closes. All timestamps in the event ledger use the observation time, not the hidden pivot time.

Equal-price ties do not create a swing in the primary contract.

## Volatility scale

ATR20 uses completed D1 true ranges only.

Primary structural tolerances:

- double-bottom/top tolerance: 0.20 ATR20;
- break buffer: 0.05 ATR20;
- retest band around the broken neckline: ±0.15 ATR20;
- minimum separation between the two bottoms/tops: 5 D1 bars;
- maximum separation: 60 D1 bars;
- maximum wait from break of structure to retest: 20 D1 bars;
- maximum wait from higher-low confirmation to continuation higher high: 30 D1 bars.

These values are frozen for the primary study. No continuous optimization is allowed.

## Bullish sequence

### State B0 — neutral

No active bullish candidate.

### State B1 — first bottom

A confirmed swing low `L1` exists.

### State B2 — double bottom candidate

A later confirmed swing low `L2` satisfies:

- 5–60 bars after `L1`;
- `abs(L2 - L1) <= 0.20 * ATR20_at_L2`;
- at least one confirmed swing high exists between L1 and L2.

The highest confirmed swing high between the bottoms is the neckline `N`.

### State B3 — break of structure

A completed D1 close exceeds:

`N + 0.05 * ATR20`

The break bar's high becomes `BOS_HIGH`.

A wick above the neckline without a qualifying close does not count.

### State B4 — retest in progress

After the break, price enters the neckline retest band:

`N ± 0.15 * ATR20`

The retest must occur within 20 completed D1 bars after the break.

The candidate is invalidated before confirmation if a completed D1 close falls below:

`min(L1, L2) - 0.05 * ATR20`

### State B5 — higher low confirmed

A confirmed swing low `HL` forms after the break and satisfies:

- `HL > max(L1, L2)`;
- the swing overlaps or follows a valid neckline retest;
- the candidate has not been structurally invalidated.

The higher low becomes observable only after its two-bar right-side confirmation delay.

### State B6 — bullish trend confirmed

After B5, a completed D1 close exceeds:

`BOS_HIGH + 0.05 * ATR20`

This is the continuation higher high. The bullish trend begins at this close, not at the original break of structure.

The active structural floor is the confirmed higher low.

### State B7 — bullish trend active

The trend remains bullish while completed D1 closes remain above the active structural floor.

Later higher-low/higher-high sequences may trail the structural floor upward. That trailing logic is diagnostic in v0.1 and may not change the original trend-start outcome.

### Bullish invalidation

A bullish trend ends when either:

- a completed D1 close is below the active higher low minus 0.05 ATR20; or
- a complete bearish sequence reaches its own confirmed-trend state.

Moving-average compression may downgrade trend health but cannot reverse the structural direction.

## Bearish sequence

Mirror all bullish rules:

- two swing highs within 0.20 ATR20;
- intervening swing low is the neckline;
- completed close below neckline minus 0.05 ATR20 is the break of structure;
- retest of the neckline band;
- confirmed lower high below both tops;
- completed close below the break low minus 0.05 ATR20 confirms the bearish trend;
- structural ceiling is the confirmed lower high.

## Candidate collision policy

Bullish and bearish candidates may coexist before either reaches confirmed trend.

When one side reaches confirmed trend:

- the opposite unconfirmed candidate is cancelled;
- the opposite side must build a new sequence from subsequently confirmed swings.

No same-bar dual confirmation is permitted. If both directions would confirm on one D1 bar because of extreme range, the state is `AMBIGUOUS_SHOCK` and direction is abstention until a later clean confirmation.

## H4 moving-average health

Primary averages:

- EMA21;
- EMA55;
- EMA200.

Primary H4 volatility scale: ATR20.

### Bullish health metrics

- ordering: EMA21 > EMA55 > EMA200;
- fast gap: `(EMA21 - EMA55) / ATR20`;
- slow gap: `(EMA55 - EMA200) / ATR20`;
- EMA21 slope over three completed H4 bars;
- EMA55 slope over three completed H4 bars;
- fast-gap change over three completed H4 bars;
- slow-gap change over three completed H4 bars.

### Bullish health states

`BULL_EXPANDING`

- bullish ordering;
- EMA21 and EMA55 slopes positive;
- both normalized gaps positive;
- fast gap increasing;
- slow gap non-decreasing.

`BULL_STABLE`

- bullish ordering;
- EMA21 and EMA55 slopes non-negative;
- gaps positive;
- expansion condition not met.

`COMPRESSED`

- EMA21/55 gap below 0.10 ATR20 or EMA55/200 gap below 0.10 ATR20;
- no opposite ordering.

`CONFLICTED`

- ordering is not aligned with the confirmed D1 direction; or
- EMA21 and EMA55 slopes are opposite the confirmed D1 direction.

Bearish states are mirrored.

## Output ledger

For each completed D1 bar, store:

- observed timestamp;
- structural state;
- confirmed direction;
- L1/L2 or H1/H2 values and observation timestamps;
- neckline;
- break timestamp and break extreme;
- retest timestamp;
- higher-low/lower-high timestamp and value;
- trend-confirmation timestamp;
- active structural floor/ceiling;
- invalidation timestamp and reason;
- last completed H4 health state;
- all ATR-scaled distances used by the state machine.

## Non-repainting guarantee

- no unconfirmed swing is used;
- no state is backdated to the hidden pivot bar;
- only completed D1 and H4 bars are consumed;
- higher-timeframe values are forward-filled only after their source bars close;
- no future month high, low or close enters current monthly levels.
