# Wayne Direction-First Framework — Preregistration v0.1

Date: 2026-07-27  
Branch: `agent/wayne-direction-first-research`

## Research question

Can a causal direction stack built from macro, regime, seasonality and confirmed market structure identify months in which an FX pair has a credible directional path from a monthly pivot zone toward monthly M4/R2 or M1/S2?

The study is not a test of whether daily pivots predict direction. Daily pivots are optional tactical context and cannot authorize or veto the direction programme.

## Strategic hierarchy

1. **Direction** — macro, regime, seasonality and confirmed D1 structure.
2. **Trend health** — completed H4 moving-average ordering, slope and divergence.
3. **Location and reach** — monthly pivot buy/sell zone and monthly targets.
4. **Execution** — blocked until the first three layers are frozen and validated.

Monthly pivots describe location and potential reach. They do not create direction.

## Universe and development period

Primary FX pairs:

- AUDUSD;
- EURUSD;
- GBPUSD;
- USDCAD;
- USDCHF;
- USDJPY.

Primary development period: 2015–2021.  
The first programme must not inspect 2022–2025 outcomes.

## Causal calendars

- D1 bars: New York 17:00 to 17:00, DST-safe.
- H4 bars: six completed four-hour bars nested inside each New York pivot day.
- Monthly bars: completed New York pivot days assigned to the local calendar month.
- Every feature is sampled from completed bars only.

## Direction layers

### 1. Structural trend — mandatory

Bullish direction requires the completed sequence:

1. double bottom;
2. higher-high break of structure above the intervening neckline;
3. retrace/retest;
4. confirmed higher low;
5. subsequent higher high.

The bearish sequence is mirrored.

The trend becomes `CONFIRMED_BULL` or `CONFIRMED_BEAR` only at step 5. A break of structure by itself is not a trend.

### 2. H4 trend health — quality, not direction

Primary moving averages: EMA 21, EMA 55 and EMA 200.

A healthy bullish trend requires:

- EMA21 > EMA55 > EMA200;
- positive EMA21 and EMA55 slopes;
- positive ATR-normalized 21/55 and 55/200 gaps;
- gaps stable or expanding, preferably expanding.

The bearish definition is mirrored.

H4 averages may grade a confirmed D1 trend as expanding, stable, compressed or conflicted. They cannot manufacture direction when D1 structure is unconfirmed.

### 3. Macro — independent directional evidence

The macro contract will use point-in-time pairwise currency differentials. Candidate families are:

- central-bank stance and expected-rate differential;
- inflation and growth-surprise differential;
- real-yield or rate-market differential;
- risk-regime sensitivity for safe-haven and commodity currencies.

No revised macro series may be used as if it were known contemporaneously. Macro remains `UNAVAILABLE` until a point-in-time data source, release timestamp and revision policy are frozen.

### 4. Regime — permission layer

Regime determines whether trend-following is permitted, degraded or blocked. It is separate from trend direction.

Initial regime families:

- volatility: compressed, normal, expanding or shock;
- directional efficiency: trend-permitting or mean-reverting;
- cross-asset risk: risk-on, neutral or risk-off;
- monetary-policy phase: easing, neutral, tightening or transition.

### 5. Seasonality — prior, not override

Seasonality is computed with an expanding historical window using only prior years. It may support, conflict with or remain neutral to the structural direction.

Initial calendar states:

- month of year;
- week of month;
- turn-of-month window;
- weekday as a diagnostic only.

Seasonality cannot override an unconfirmed or opposite structural trend.

## Direction triage

The initial router is categorical rather than a tunable weighted score.

### Long candidate

- D1 structure is `CONFIRMED_BULL`;
- macro is bullish or neutral, never bearish;
- regime permits trend-following;
- seasonality is bullish or neutral;
- H4 health is expanding or stable bullish.

### Short candidate

Mirror of the long candidate.

### Abstain

Any of the following produces abstention:

- D1 structure is not confirmed;
- macro and structure conflict;
- regime is mean-reverting or shock without a frozen exception;
- H4 moving averages are conflicted;
- seasonality strongly opposes and no separate conflict study has been authorized.

No post-hoc weighting rescue is allowed in the first programme.

## Monthly location and reach

Traditional monthly levels are computed from the completed prior month's high, low and close:

- P, R1, S1, R2, S2;
- M1–M4 as exact midpoints between adjacent principal levels.

### Bullish opportunity

- primary location: month opens in the monthly M2–P buy zone;
- diagnostic location: first touch of M2–P during the first five pivot days;
- conservative reach: monthly M4;
- stretch reach: monthly R2;
- monthly R1 is recorded as an intermediate checkpoint.

### Bearish opportunity

Mirror definition:

- P–M3 sell zone;
- M1 conservative reach;
- S2 stretch reach;
- S1 intermediate checkpoint.

Reach is evaluated only after direction exists. The primary outcome is target reached before month-end and before structural trend invalidation. Pivot-zone entry prices are not treated as executable fills in this stage.

## Research sequence

1. Implement and validate the causal D1 structural state machine.
2. Implement H4 EMA health and divergence states.
3. Implement monthly pivot location and reach ledger.
4. Freeze seasonality states and expanding-window computation.
5. Qualify point-in-time macro and regime sources.
6. Build the direction triage ledger.
7. Evaluate conditional monthly reach before any entry or stop optimization.
8. Open bounded execution research only if direction and reach pass breadth and stability gates.

## Evidence requirements

A direction/reach state may advance only if it has:

- at least 300 pooled observations;
- at least 40 observations in four or more pairs;
- positive effect in at least four development years;
- no single pair above 40% of positive contribution;
- no single year above 30% of positive contribution;
- positive stressed economic proxy;
- date-block bootstrap probability of positive effect at least 90%;
- FDR-adjusted q-value no greater than 0.10 where a family is tested.

## Explicit exclusions

The first programme does not authorize:

- daily-pivot optimization;
- M15 entry optimization;
- continuous search over swing tolerances or MA lengths;
- partial exits, runners or breakeven rules;
- pair/day/year post-hoc selection;
- 2022–2025 outcome inspection;
- Pine implementation, alerts, sizing, paper trading or deployment.

## Interpretation boundary

A positive result means the frozen direction stack identifies a reproducible conditional monthly path. It does not prove an executable strategy until bid/ask execution, costs, stops and entries are separately frozen and tested.
