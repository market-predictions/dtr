# Stacey Burke Conditional Sweep/Reclaim Study — Preregistration

Version: `v1.0.0`  
Date frozen: `2026-07-24`  
Work package: `SB-WP-20260724-02`  
Status: `FROZEN_BEFORE_EVENT_COUNT_INSPECTION`

## Research question

Does a mechanically defined previous-FX-day high or low sweep followed by a prompt reclaim during the London opening window occur often and broadly enough to support a pooled, controlled event study across the fixed ten-pair FX universe?

This phase is an event census only. It cannot inspect forward returns, define entries, stops or targets, calculate strategy P&L, select pairs, or tune thresholds.

## Frozen universe and partitions

Universe:

- EURUSD, GBPUSD, USDCHF;
- AUDUSD, NZDUSD, USDCAD;
- USDJPY, EURJPY, GBPJPY;
- EURGBP.

Partitions:

- 2015–2021: discovery census and, only after the census gate passes, controlled event study;
- 2022–2023: validation only;
- 2024–2025: untouched holdout;
- 2026 YTD through 2026-07-23: monitoring only.

No result from 2022 onward may influence the event definition.

## Frozen market clock

### FX trading day

The FX trading day runs from 17:00 inclusive to 17:00 exclusive in `America/New_York`, with daylight-saving transitions handled by the timezone database.

A trading date is the New York calendar date on which that FX day ends. Previous-day levels are built only from the completed preceding FX trading date.

### London event window

The event window is 07:00 inclusive to 10:00 exclusive in `Europe/London`, with daylight-saving transitions handled by the timezone database.

The window is anchored to London local time. A fixed-UTC window is not a co-primary configuration and has no gate authority.

## Frozen price series

Event detection uses synchronized active one-minute midpoint OHLC:

- midpoint open = `(bid open + ask open) / 2`;
- midpoint high = `(bid high + ask high) / 2`;
- midpoint low = `(bid low + ask low) / 2`;
- midpoint close = `(bid close + ask close) / 2`.

The midpoint prevents the spread alone from manufacturing a high or low sweep. BID and ASK remain mandatory for source integrity and for any later executable strategy simulation.

## Previous-day reference levels and normalization

For each completed FX trading date:

- previous-day high = maximum active midpoint high;
- previous-day low = minimum active midpoint low;
- previous-day close = final active midpoint close;
- true range = maximum of high-minus-low, absolute high-minus-previous-close, and absolute low-minus-previous-close;
- ATR20 = arithmetic mean of the preceding 20 completed FX-day true ranges, excluding the current trading date.

A session is ineligible unless its previous-day high, previous-day low and ATR20 are fully known before the London window begins.

Appending future bars must not change any already calculated reference level or event.

## Frozen event definition

The definition is symmetric.

### Previous-day high sweep and reclaim

1. Inside the London event window, active midpoint high reaches at least:

   `previous-day high + 0.05 × ATR20`.

2. The first minute satisfying that excursion starts a non-resetting 15-minute reclaim clock.
3. On the sweep minute or within the following 15 one-minute bars, active midpoint close is at or below the previous-day high.
4. The event direction is `short_reversal`.

### Previous-day low sweep and reclaim

1. Inside the London event window, active midpoint low reaches at most:

   `previous-day low - 0.05 × ATR20`.

2. The first minute satisfying that excursion starts a non-resetting 15-minute reclaim clock.
3. On the sweep minute or within the following 15 one-minute bars, active midpoint close is at or above the previous-day low.
4. The event direction is `long_reversal`.

### Event selection rules

- The excursion threshold and reclaim delay are fixed and may not be optimized.
- A side that fails to reclaim within its first 15-minute clock cannot reset and try again that session.
- At most one event is retained per instrument and London session: the event with the earliest reclaim timestamp.
- If both sides reclaim on the same timestamp, the session is classified as directionally ambiguous and excluded from the retained event set, while remaining visible in exclusion counts.
- Same-minute sweep and reclaim is valid because the excursion occurs within the minute and the reclaim is known only at that minute's close.
- No inside-day, weekday, trend, volatility-regime, candle-shape, displacement, round-number, three-day-cycle, or pair-specific filter is permitted in the primary census.

## Session quality rules

A London session is eligible only when:

- at least 171 of its 180 expected one-minute timestamps have synchronized active BID and ASK quotes;
- its prior reference day contains active midpoint observations;
- ATR20 is available and strictly positive;
- the reference high is above the reference low.

Excluded-session and ambiguous-session counts must be reported. Missing or inactive minutes may not be synthetically filled.

## Required event ledger

Every retained event records at least:

- symbol and factor block;
- trading date and London local date;
- swept side and reversal direction;
- previous-day high, low and ATR20;
- excursion threshold;
- first sweep timestamp;
- reclaim timestamp and reclaim delay in minutes;
- sweep extreme;
- excursion in price, pips and ATR units;
- reclaim close and distance back through the reference level;
- same-minute-reclaim flag;
- synchronized active-minute coverage;
- source partition labels.

No forward-return or P&L field is allowed in the Phase 1 ledger.

## Phase 1 census gate

The census passes only if every predicate is true on 2015–2021:

1. at least 100 pooled retained events;
2. at least 8 of 10 pairs contribute at least 5 retained events each;
3. all four frozen factor blocks contribute at least 10 retained events each;
4. no single pair contributes more than 30% of pooled events;
5. no single London calendar date contributes more than 10% of pooled events;
6. all unit, causality, DST and future-append invariance tests pass.

Failure stops the Stacey Burke reversal programme. Thresholds may not be relaxed after seeing the count.

## Predeclared controlled event-study gate

Only if the census passes, the primary discovery endpoint is the reversal-signed 60-minute midpoint return from the reclaim close, divided by pre-event ATR20.

The primary comparison is against deterministic matched non-event controls from the same instrument, year, weekday and 15-minute London time bucket, with nearest matching on pre-event 15-minute return and trailing 60-minute realized volatility. Five controls are selected per event without using future returns.

Gate B requires all of the following on 2015–2021:

1. at least 400 retained events with an observable 60-minute endpoint;
2. mean event-minus-control return of at least `+0.02 ATR20`;
3. a 95% calendar-date block-bootstrap confidence interval whose lower bound is above zero;
4. a calendar-date label-permutation p-value no greater than 0.05;
5. positive point estimates for at least 7 of 10 pairs;
6. positive point estimates for at least 3 of 4 factor blocks.

The bootstrap and permutation unit is the London calendar date, preserving same-day cross-pair dependence. The trial budget is one primary configuration, one primary horizon and one primary endpoint. Additional horizons or thresholds are exploratory and cannot authorize SB-1.

## Power statement

For a control-adjusted 60-minute return standard deviation of `0.30 ATR20`, a two-sided 5% test with 80% power has an approximate minimum detectable mean of:

- `0.084 ATR20` at 100 events;
- `0.042 ATR20` at 400 events;
- `0.027 ATR20` at 1,000 events.

The 100-event census floor is therefore only a feasibility kill gate. It is not sufficient evidence of a tradable effect. Gate B separately requires at least 400 events and a positive blocked interval.

## Explicit exclusions

Until Gate B passes, the programme may not:

- create an executable SB-1 strategy;
- inspect stop, target or R-multiple performance;
- optimize the session, excursion, reclaim delay or forward horizon;
- add an inside-day or other Burke narrative condition;
- select or drop pairs based on event behaviour;
- inspect 2022–2025 returns;
- build Pine, alerts, sizing, paper trading or deployment.

The programme exists to test and potentially reject the methodology, not to preserve it.