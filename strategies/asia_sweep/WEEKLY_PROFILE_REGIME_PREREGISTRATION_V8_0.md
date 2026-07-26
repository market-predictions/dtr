# Asian Sweep Weekly-Profile and Trend-Regime Study — Preregistration v8.0

Date frozen: 2026-07-26  
Branch: `agent/asia-sweep-weekly-profile-regime`  
Development sample: EURUSD and GBPUSD, 2015–2019  
Protected sample: 2020–2025 unopened

## 1. Research question

The completed extended-reversal programme rejected unconditional Asian Sweep execution. This new programme asks a materially different question:

> Does a causal higher-timeframe trend and developing weekly profile identify Asian Sweep events that represent either (a) resumption of the structural trend after an early-week countertrend retracement or (b) continuation of that early-week retracement, with positive executable target geometry?

This is not a filter rescue of the rejected 40-candidate study. It is a new hierarchical market hypothesis:

`structural trend -> developing weekly path -> session sweep -> action and target`.

## 2. Scientific boundary

- Use only qualified EURUSD and GBPUSD BID/ASK minute data from 2015–2019.
- Use the immutable T0 extended-target outcomes already produced by the authoritative extended-reversal run.
- Do not inspect 2020–2025.
- Do not optimize regime thresholds after viewing outcomes.
- Do not rescue by pair, year, weekday, sweep direction, threshold, target, landmark, stop or model family.
- Do not open continuation/reversal routing models unless the mechanism gate passes.
- Do not open position-structure P&L, Pine, alerts, paper trading or deployment in this phase.

## 3. Causal timing

All daily and weekly-profile features must be known strictly before the event entry timestamp.

- Daily features use completed local trading days only.
- Current-week features use active quotes from Monday 00:00 Europe/Amsterdam up to, but excluding, the event entry timestamp.
- No completed-week high, low, close or future weekly label may be used.
- The event bar itself is excluded from weekly context.

## 4. Structural-trend definition

Context is based on midpoint daily bars.

For each event day, using data through the preceding completed day:

- `d20_return_atr = (close[D-1] - close[D-21]) / ATR20`;
- `close_vs_sma20_atr = (close[D-1] - SMA20[D-1]) / ATR20`;
- `sma20_slope_5d_atr = (SMA20[D-1] - SMA20[D-6]) / (5 * ATR20)`;
- `efficiency20 = abs(close[D-1] - close[D-21]) / sum(abs(daily close changes), 20 sessions)`.

Directional score:

- add `+1` when `d20_return_atr > +0.50`, `-1` when below `-0.50`;
- add `+1` when `close_vs_sma20_atr > +0.25`, `-1` when below `-0.25`;
- add `+1` when `sma20_slope_5d_atr > +0.01`, `-1` when below `-0.01`.

State:

- `UP` when score >= +2;
- `DOWN` when score <= -2;
- otherwise `NEUTRAL`.

Strength is `STRONG` when the state is directional, `abs(d20_return_atr) >= 1.50` and `efficiency20 >= 0.35`; otherwise a directional state is `MODERATE`.

## 5. Developing-week measurements

At the event timestamp:

- weekly open: first active midpoint open from Monday 00:00 Amsterdam;
- current price: last active midpoint close before entry;
- current-week high and low: extrema before entry;
- `price_vs_week_open_atr`;
- `withtrend_excursion_atr`;
- `countertrend_excursion_atr`;
- `recovery_from_countertrend_extreme_atr`;
- `current_week_range_atr`;
- distance to Monday high and low in ATR;
- prior-week return in ATR and prior-week close location;
- current countertrend excursion as a fraction of the absolute prior-week return where defined.

Current-week direction is:

- `UP` at >= +0.15 ATR from weekly open;
- `DOWN` at <= -0.15 ATR;
- otherwise `FLAT`.

## 6. Frozen weekly-phase taxonomy

Priority order:

1. `WEEKLY_ROTATION` when structural trend is neutral.
2. `EARLY_WEEK_COUNTERTREND_RETRACE` on Monday or Tuesday when current-week direction opposes structural trend and countertrend excursion >= 0.20 ATR.
3. `EARLY_WEEK_TREND_EXTENSION` through Wednesday when with-trend excursion >= 0.35 ATR and countertrend excursion < 0.20 ATR.
4. `MIDWEEK_TREND_RESUMPTION` through Wednesday when countertrend excursion >= 0.35 ATR and recovery from the countertrend extreme >= 0.20 ATR.
5. `MIDWEEK_REVERSAL_OR_TRANSITION` from Wednesday onward when countertrend excursion >= 0.75 ATR and current-week direction still opposes structural trend.
6. `LATE_WEEK_EXPANSION` on Thursday or Friday when either directional excursion >= 0.75 ATR.
7. Otherwise `WEEKLY_ROTATION`.

## 7. Frozen trade-role taxonomy

A lower sweep implies a proposed long reversal; an upper sweep implies a proposed short reversal.

Priority order:

1. `HTF_TREND_RESUMPTION`: Monday–Wednesday, proposed trade aligns structural trend, countertrend excursion >= 0.35 ATR, with-trend excursion < 0.75 ATR.
2. `WEEKLY_RETRACE_CONTINUATION`: Monday–Tuesday, proposed trade opposes structural trend, current-week direction also opposes structural trend, countertrend excursion >= 0.20 ATR, with-trend excursion < 0.50 ATR.
3. `EARLY_WEEK_TREND_EXTENSION`: Monday–Wednesday, proposed trade aligns structural trend, with-trend excursion >= 0.35 ATR, countertrend excursion < 0.20 ATR.
4. `EXHAUSTION_REVERSAL`: proposed trade opposes structural trend after with-trend excursion >= 0.75 ATR.
5. `MATURE_TREND_EXTENSION`: proposed trade aligns structural trend after with-trend excursion >= 0.75 ATR or on Thursday/Friday.
6. Otherwise `ROTATION_OR_AMBIGUOUS`.

## 8. Hypotheses and fixed target hierarchies

### H1 — Structural-trend resumption

After an observable early-week countertrend excursion, a sweep reversal aligned with the structural trend has superior target probability and positive stressed expected-value proxy.

Reference population: T0 events on Monday–Wednesday with a non-neutral structural trend and proposed reversal aligned with that trend, without requiring the countertrend-excursion condition.

Target hierarchy, first passing target wins:

1. `EXT_OPPOSITE_BOUNDARY_1100`;
2. `EXT_FIXED_2R_1100`;
3. `EXT_OPPOSING_LIQUIDITY_1400`;
4. `EXT_FIXED_3R_1200`;
5. `EXT_FIXED_4R_1400`.

### H2 — Early-week retracement continuation

While Monday/Tuesday remains displaced countertrend to the structural trend, a sweep reversal aligned with that active retracement can have positive shorter-horizon economics.

Reference population: T0 events on Monday–Tuesday with a non-neutral structural trend and proposed reversal opposing that trend, without requiring active countertrend displacement.

Target hierarchy, first passing target wins:

1. `EXT_FIXED_2R_1100`;
2. `EXT_OPPOSITE_BOUNDARY_1100`;
3. `EXT_FIXED_3R_1200`;
4. `EXT_OPPOSING_LIQUIDITY_1400`;
5. `EXT_FIXED_4R_1400`.

H1 has programme priority over H2. H2 may open a separate modelling route only if H1 has no passing target and H2 independently passes all gates.

## 9. Mechanism metrics

For each hypothesis-target population at T0:

- eligible events and positive cases;
- observed target rate;
- absolute and relative target-rate lift versus the frozen reference population;
- median stressed reward/risk;
- fraction retaining at least 1.25R;
- observed stressed EV proxy per row: `hit * stressed_RR - (1 - hit)`;
- pair-level and year-level lift and EV proxy;
- maximum pair and year concentration.

Non-hits are treated as `-1R` in the EV proxy, matching the binary target-gate convention of the preceding programme.

## 10. Frozen mechanism gates

### H1 gates

All must pass:

- at least 150 pooled events and 30 positives;
- at least 50 events in each pair;
- absolute target-rate lift >= 5 percentage points;
- relative target-rate lift >= 1.25x;
- pooled observed stressed EV proxy > 0;
- positive observed stressed EV proxy in both pairs;
- positive observed stressed EV proxy in at least 3 of 5 years;
- positive target-rate lift in both pairs and at least 4 of 5 years;
- median stressed reward/risk >= 1.25R;
- at least 75% of events retain stressed reward/risk >= 1.25R;
- no pair contributes more than 70% of events;
- no year contributes more than 40% of events.

### H2 gates

All must pass:

- at least 120 pooled events and 25 positives;
- at least 40 events in each pair;
- absolute target-rate lift >= 4 percentage points;
- relative target-rate lift >= 1.20x;
- pooled observed stressed EV proxy > 0;
- positive observed stressed EV proxy in both pairs;
- positive observed stressed EV proxy in at least 3 of 5 years;
- positive target-rate lift in both pairs and at least 4 of 5 years;
- median stressed reward/risk >= 1.25R;
- at least 75% retain stressed reward/risk >= 1.25R;
- pair concentration <= 70%;
- year concentration <= 40%.

## 11. Decision rule

- Evaluate H1 targets in frozen order. Select the first target passing all H1 gates.
- Only if H1 has no passing target, evaluate H2 targets in frozen order and select the first passing target.
- If one target passes: `PASS_WEEKLY_PROFILE_MECHANISM_OPEN_MODELING`.
- If none passes: `FAIL_WEEKLY_PROFILE_MECHANISM_STOP`.

Descriptive results for failed targets may be reported but may not be used to alter thresholds or reorder targets.

## 12. Conditional next phase

Only after a mechanism pass:

- freeze a minimal regime-aware challenger against the existing feature baseline;
- use leave-one-year-out evaluation and Amsterdam-week grouped tuning;
- require incremental discrimination, calibration, pair/year breadth and positive stressed EV;
- then and only then consider reversal/continuation/abstention routing.

Protected 2020–2025 remains closed until the complete development architecture passes.