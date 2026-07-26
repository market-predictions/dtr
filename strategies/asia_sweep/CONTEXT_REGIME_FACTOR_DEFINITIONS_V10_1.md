# Asian Sweep Context and Regime Atlas — Factor Definitions v10.1

Date frozen: 2026-07-26  
Parent contract: `CONTEXT_REGIME_ATLAS_PREREGISTRATION_V10_0.md`

This amendment freezes exact causal definitions before any context-atlas outcome is inspected.

## Clock and source convention

- raw EURUSD and GBPUSD midpoint M1 built from synchronized Dukascopy BID/ASK;
- all regime aggregation uses `Europe/Amsterdam` wall-calendar boundaries;
- only rows with active BID and ASK quotes are used;
- a completed daily bar requires at least 1,200 active minutes;
- daily features for trade date `D` use completed daily bars strictly before `D`;
- weekly features use completed ISO weeks strictly before the event week;
- the event context anchor is the final active midpoint close in `[00:00, 08:00)` Amsterdam;
- no sweep-bar, T5 or post-event price enters a pre-event regime feature.

## Structural direction

### D1 structural direction

Compute completed-day close returns over five and twenty valid daily bars:

- `UP`: both returns are positive;
- `DOWN`: both returns are negative;
- `MIXED`: signs disagree or either return is zero;
- `WARMUP`: either horizon is unavailable.

### W1 structural direction

Compute completed-week close returns over one and four valid completed ISO weeks:

- `UP`: both returns are positive;
- `DOWN`: both returns are negative;
- `MIXED`: signs disagree or either return is zero;
- `WARMUP`: either horizon is unavailable.

### Direction relations

The reversal direction is `DOWN` after an `UP` sweep and `UP` after a `DOWN` sweep.

For D1 and W1 independently:

- `ALIGNED`: reversal direction equals structural direction;
- `OPPOSED`: reversal direction opposes structural direction;
- `MIXED`: structural direction is mixed;
- `WARMUP`: structural direction is unavailable.

D1/W1 agreement is `ALIGNED_UP`, `ALIGNED_DOWN`, `CONFLICT`, `MIXED`, or `WARMUP`.

## Trend strength

### Daily normalized slope

Fit an ordinary least-squares slope to the last 20 completed daily closes. Normalize as:

`20 * slope / ATR20`

Strength state:

- `WEAK`: absolute normalized slope < 0.75;
- `MODERATE`: 0.75 through < 2.00;
- `STRONG`: >= 2.00;
- `WARMUP`: unavailable.

### Weekly normalized slope

Fit OLS to the last eight completed weekly closes. Normalize as:

`8 * slope / median completed-week range over the previous 20 weeks`

Use the same weak/moderate/strong thresholds.

### Daily directional efficiency

`abs(close[-1] - close[-20]) / sum(abs(daily_close_change))` over the same 20 completed daily bars.

- `ROTATIONAL`: < 0.25;
- `ORDERED`: 0.25 through < 0.50;
- `PERSISTENT`: >= 0.50;
- `WARMUP`: unavailable.

## Trend change

Compare the mean signed daily change over the most recent five completed days with the mean signed change over the most recent twenty completed days.

- `CONFLICT`: signs differ;
- `ACCELERATING`: same sign and absolute five-day rate > 1.25 times the twenty-day rate;
- `DECELERATING`: same sign and absolute five-day rate < 0.75 times the twenty-day rate;
- `STABLE`: same sign and neither acceleration threshold is met;
- `FLAT`: the twenty-day rate is effectively zero relative to ATR20 (`abs(rate20) <= 0.01 * ATR20`);
- `WARMUP`: unavailable.

Trend change never replaces structural direction. For example, positive acceleration inside a structurally bearish D1 state is recorded as bearish structure plus improving short-horizon momentum, not an established bullish trend.

## Volatility regime

### Daily ATR percentile

ATR20 is the mean true range of the 20 completed daily bars immediately before the trade date. Its percentile is calculated against the previous 252 causal ATR20 values, with a minimum of 60.

### Weekly range percentile

The most recently completed weekly range is ranked against the previous 52 completed weekly ranges, with a minimum of 20.

### Short realized-volatility percentile

Five-day realized close-to-close volatility is ranked against its previous 126 causal observations, with a minimum of 40.

Percentile states:

- `COMPRESSED`: <= 30th percentile;
- `NORMAL`: >30th and <70th percentile;
- `EXPANDED`: >=70th percentile;
- `WARMUP`: unavailable.

### Volatility transition

Compare current ATR20 with ATR20 five completed daily bars earlier:

- `RISING`: ratio > 1.10;
- `FALLING`: ratio < 0.90;
- `STABLE`: otherwise;
- `WARMUP`: unavailable.

The existing causal Asian-range percentile-60 bucket remains unchanged and is reported as a separate session-volatility factor.

## Causal location

All location calculations use the 08:00 context anchor.

### Prior-day and prior-week range position

`(anchor - low) / (high - low)`

State:

- `BELOW` for values < 0;
- `LOWER` for 0 through < 1/3;
- `MIDDLE` for 1/3 through < 2/3;
- `UPPER` for 2/3 through <= 1;
- `ABOVE` for values > 1;
- `WARMUP` when unavailable.

### Nearest boundary distance

Minimum absolute distance to high or low, divided by ATR20:

- `NEAR`: <= 0.25 ATR;
- `INTERMEDIATE`: >0.25 through <=0.75 ATR;
- `FAR`: >0.75 ATR;
- `WARMUP`: unavailable.

### Open displacement

- daily-open displacement: anchor minus Amsterdam daily open, divided by ATR20;
- weekly-open displacement: anchor minus current ISO-week open, divided by ATR20;
- overnight gap: daily open minus previous valid daily close, divided by ATR20.

Signed displacement is retained continuously and also bucketed as `DOWN`, `FLAT`, or `UP` using a fixed +/-0.25 ATR dead zone.

### Monday range position

Available only from Tuesday onward and based only on the completed Monday daily bar. It uses the same range-position states.

## Primary population and payoff proxy

The primary atlas population is the frozen T5 population produced by `build_population(events, "T5")`:

- T5 available;
- unresolved at the T5 decision point according to the frozen fingerprint contract;
- target `midpoint_success_09_10` unchanged.

The economic proxy is binary and deliberately conservative:

- success payoff equals the remaining midpoint reward divided by the stressed risk at the actual next active T5 BID/ASK open;
- failure payoff equals `-1R`;
- entry and stop each receive the unchanged 0.10-pip adverse stress;
- the original stop remains 0.20 Asian-range beyond the sweep extreme;
- events with non-positive remaining reward or risk are excluded from economic attribution but remain in classification attribution.

This is a selection/payoff proxy, not an execution-strategy P&L simulation.

## Single-factor testing

- all listed states are tested; no state is dropped after seeing outcomes;
- each state is compared with the full eligible population, not with a selectively chosen opposite state;
- date is the bootstrap block;
- 5,000 deterministic bootstrap draws, seed `20260726`;
- two-sided permutation p-values use 5,000 date-block label permutations;
- Benjamini-Hochberg false-discovery-rate correction is applied across every tested state in the complete single-factor atlas;
- no state may pass on classification lift alone; stressed economic effect, pair breadth, year breadth and concentration gates remain mandatory.

## Interaction selection

The six interaction slots, if authorized, are selected mechanically:

1. rank passing or near-passing factor families by their best preregistered state evidence score;
2. exclude factors sharing the same underlying input series;
3. choose the highest-ranked non-redundant cross-family pairs;
4. freeze those pairs before calculating interaction outcomes.

No manual interaction substitution is permitted after outcomes are visible.
