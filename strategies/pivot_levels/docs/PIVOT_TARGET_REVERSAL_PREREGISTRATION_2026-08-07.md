# Pivot Levels Target / Stall / Reversal Study — Preregistration

Date: 2026-08-07
Programme: `PIVOT-TARGET-REVERSAL-V1`
Work package: `PIV-WP-20260807-01`

## Research question

Do classic floor pivot levels act as statistically distinctive price targets, containment/stall zones, trend-leg endpoints, or reversal zones relative to nearby non-pivot price coordinates?

This is a new pivot-level programme. It does not inherit Wayne directional-bias logic and it is not a rescue of the failed Quarters Theory grid.

## Data contract

- Canonical source: registered `Dukascopy FX Cache` in `data/private_market_data_cache_registry.json`.
- Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Construction: Dukascopy M1, separate BID/ASK, UTC; midpoint used for structural research.
- Development: 2015–2019 where prior-period data exist.
- Internal validation: 2020–2021.
- Holdout: 2022–2025 remains unopened.
- No historical data reacquisition is authorized.
- Native source pip units are retained: 0.0001 for non-JPY pairs and 0.01 for JPY pairs.

## FX period boundary

The trading-day boundary is 17:00 America/New_York, DST-safe.

An FX trading day is labelled by the calendar date on which its 17:00 New York close occurs. Weekly periods end Friday at 17:00 New York. Monthly, quarterly and yearly periods use the corresponding FX trading-day calendar label, so the first post-17:00 session belongs to the next FX day/month/quarter/year where applicable.

Only a fully completed prior period may generate pivots for the current period.

## Pivot formula — frozen classic floor pivots

From prior-period high `H`, low `L`, close `C`:

- `PP = (H + L + C) / 3`
- `R1 = 2*PP - L`
- `S1 = 2*PP - H`
- `R2 = PP + (H - L)`
- `S2 = PP - (H - L)`
- `R3 = H + 2*(PP - L)`
- `S3 = L - 2*(H - PP)`

Daily and weekly test levels: `S3, S2, S1, PP, R1, R2, R3`.

Monthly, quarterly and yearly additionally test the six exact arithmetic midlevels between adjacent principal pivots:

- `MID_S3_S2`
- `MID_S2_S1`
- `MID_S1_PP`
- `MID_PP_R1`
- `MID_R1_R2`
- `MID_R2_R3`

No other pivot formulas, Fibonacci pivots, Camarilla levels, CPR bands, opening-range pivots or developing pivots are in scope.

## Nearby-placebo controls

Each real pivot level receives two local placebo coordinates at `level ± 0.25 * local_spacing`, where `local_spacing` is the smaller positive distance to the adjacent tested pivot level; at an outer level the sole adjacent spacing is used.

The placebo coordinates are data-independent and are not themselves pivot levels. For monthly and higher timeframes, because midlevels are real tested levels, the placebo coordinates are therefore quarter-subdivisions of the already denser real-level lattice.

The comparison asks whether the exact pivot coordinate matters, rather than whether price reacts somewhere in the same broad area.

## Causal volatility and tolerance zone

A prior 20-FX-day ATR is calculated from completed daily midpoint candles and lagged one trading day.

For each real level or its local placebo, define zone half-width in pips:

`zone = min(25, 0.10 * ATR20_D1, 0.10 * local_spacing)`

with a lower numerical floor of 1 pip only when the spacing permits it; zone width may be smaller than 1 pip if required to prevent overlap with neighbouring controls.

A level is considered reached when M1 high/low first enters its tolerance zone. Time spent inside the zone is neutral: price is not required to reverse immediately.

## Independent trend definition

The approach filter is identical in spirit to the prior destination study but contains no pivot information:

- five contiguous valid H1 closes spanning four hours;
- absolute four-hour displacement >= `0.75 * ATR24_H1`;
- directional efficiency >= `0.60`;
- current close in the outer 20% of the recent four-hour range;
- candidate level lies in the trend direction;
- candidate tolerance zone was not entered in the preceding four hours.

For approach episodes, distance from current close to the near edge of the level zone must be between `0.10 * ATR24_H1` and `0.75 * ATR24_H1`.

## Primary mechanism tests

### P0 — Fresh period touch census (descriptive)

For every timeframe and named real level, estimate:

- number of eligible active periods;
- fresh-touch rate after excluding levels already inside the tolerance zone at period open;
- median time from period open to first touch;
- development and validation touch rates separately.

P0 is descriptive and does not by itself establish pivot specificity.

### P1 — Independent trend-leg endpoint clustering

Reuse the already-frozen H1 `0.75*ATR24` directional-change trend-leg detector, which was defined without reference to pivots.

For each leg endpoint and active timeframe, compare tolerance-zone hits at each real level with its two local placebo coordinates.

Per endpoint/parent-level score:

`real_hit - 0.5*(placebo_low_hit + placebo_high_hit)`.

The timeframe score is the mean across eligible endpoint/parent-level observations. Positive values imply terminal clustering at the exact pivot coordinate.

### P2 — Trend-approach target completion

At a qualified approach event, outcome is `1` if price enters the level tolerance zone before an adverse move of `0.50 * ATR24_H1`, `-1` if the adverse barrier occurs first, and `0` for timeout/ambiguous ordering.

Observation ends at the earliest of 24 hours or expiry of the active pivot period.

Real levels are compared with their local placebos within matched strata.

### P3 — Post-touch containment / stall

After first zone entry, define a continuation barrier beyond the trend-side zone edge by `0.25 * ATR24_H1`.

A containment success is `1` if that continuation barrier is not breached during the frozen dwell window, otherwise `0`.

Dwell windows:

- daily: 60 minutes;
- weekly: 120 minutes;
- monthly: 240 minutes;
- quarterly: 360 minutes;
- yearly: 480 minutes.

This test explicitly allows sideways trade and rotation inside the tolerance zone.

### P4 — Reversal before extension after arrival

After first zone entry, define symmetric barriers outside the tolerance zone:

- reversal barrier: opposite-side zone edge plus `0.25 * ATR24_H1` away from the incoming trend;
- extension barrier: trend-side zone edge plus `0.25 * ATR24_H1` in the incoming trend direction.

Whichever barrier is reached first within 24 hours or active-period expiry determines the result:

- `+1`: reversal first;
- `-1`: extension first;
- `0`: timeout or same-minute ambiguity.

Time spent inside the tolerance zone is neutral and does not count as extension.

## Matching and inference

P2–P4 are compared real-versus-placebo using matched strata containing, where sample permits:

- pair;
- year;
- timeframe;
- parent pivot label;
- direction;
- four-hour UTC session;
- approach-distance band;
- ATR tercile within pair-year-timeframe;
- efficiency band.

P1 is evaluated through the frozen exposure-balanced score.

Uncertainty uses pair-year-week clustered bootstrap resampling. Primary run: 5,000 draws. Familywise multiplicity is controlled by Holm correction across the 20 primary timeframe/mechanism hypotheses (`P1–P4` × five timeframes).

## Promotion gate

A specific timeframe/mechanism qualifies only if all are true:

1. development and validation effects are both positive;
2. combined 95% bootstrap interval is strictly above zero;
3. Holm-adjusted two-sided p-value < 0.05;
4. at least 6 of 10 eligible pairs have positive effect direction when pair sample permits;
5. leave-one-pair-out pooled effects remain positive;
6. result is not dominated by one named level or one pair.

Higher-timeframe sample limitations are reported explicitly; no gate is relaxed after outcomes.

## Authorization boundary

This work package may identify structural target/stall/reversal information only. It does not authorize entries, stops, profit targets, execution P&L, pair shopping, threshold optimization, Pine, alerts, sizing, paper trading or deployment.

The 2022–2025 holdout may be opened only by a separate preregistered confirmation package if at least one primary mechanism passes this internal development/validation gate.