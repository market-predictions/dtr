# Preregistration — Daily Pivot × H1 Wick Protected Holdout Confirmation

Date: 2026-08-08
Study ID: `DFXC-20260808-003-pivot-daily-wick-holdout`
Parent: `DFXC-20260808-002-pivot-wick-rejection`
Dataset: **Dukascopy FX Cash**
Study type: protected holdout confirmation

## Question

Does the internally promoted Daily classic-pivot × H1 directional-wick interaction replicate unchanged on the protected 2022–2025 sample?

## Prior evidence

On exposed 2015–2021 data, the frozen interaction was +0.92 percentage point with 95% CI approximately +0.49 to +1.36 pp, development +1.13 pp, internal validation +0.39 pp, 8/10 pair effects positive and every leave-one-pair-out pooled interaction positive.

This prior estimate is context only and is not a minimum-effect target for the holdout.

## Data boundary

Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.

Outcome period: NY17 FX trading dates 2022-01-01 through 2025-12-31.

Permitted warm-up: 2021 only, strictly for H1 ATR warm-up and prior completed daily pivot construction. No 2021 observation contributes to holdout metrics. No 2026 source member may be read.

Price basis: structural midpoint of synchronized Dukascopy BID/ASK OHLC.

## Pivot construction

Classic floor pivots from the prior completed NY17 FX trading day:

- `PP = (H + L + C) / 3`
- `R1 = 2*PP - L`
- `S1 = 2*PP - H`
- `R2 = PP + (H-L)`
- `S2 = PP - (H-L)`
- `R3 = H + 2*(PP-L)`
- `S3 = L - 2*(H-PP)`

Tested levels: S3, S2, S1, PP, R1, R2, R3. No level selection.

## Current Daily pivot zone — unchanged

For each eligible H1 high and low, assign the nearest current daily pivot. Define `local_spacing` as the distance from that pivot to the adjacent tested pivot in the direction of the observation; at S3/R3 use the corresponding inward spacing. Exact ties select the lower-price level, matching the parent implementation.

Normalized distance:

`d = abs(extreme - pivot) / local_spacing`

- core: `0 <= d < 0.20`
- middle: `0.20 <= d < 0.30` (not used in primary interaction)
- outer: `0.30 <= d <= 0.50`
- observations beyond 0.50 are excluded from the primary nearest-pivot corridor.

This zone is spacing-relative and contains no ATR term.

## H1 terminal definition — unchanged and pivot-blind

On H1 midpoint bars:

1. true range uses current H/L and prior close;
2. ATR24 is a simple 24-bar mean, shifted one H1 bar;
3. directional-change threshold = `0.75 * ATR24_lag1`;
4. candidate running high/low extremes are tracked independently of pivots and wicks;
5. an extreme may be marked terminal only when a strictly later H1 candle closes at least the threshold in the opposite direction;
6. same-candle confirmation is prohibited.

## Directional wick definition — unchanged

For a high observation:

`upper_wick_fraction = (H - max(O,C)) / (H-L)`

For a low observation:

`lower_wick_fraction = (min(O,C) - L) / (H-L)`

Frozen bins:

- `<10%`
- `10–20%`
- `20–30%`
- `30–40%`
- `>=40%`

Primary classes:

- strong = wick fraction `>= 0.30`
- weak = wick fraction `< 0.10`

## Primary endpoint

`interaction = (core_strong_terminal_rate - core_weak_terminal_rate) - (outer_strong_terminal_rate - outer_weak_terminal_rate)`

This tests whether directional wick rejection carries additional terminal information inside the pivot core beyond generic wick exhaustion in the outer control region.

## Secondary diagnostics

- structural terminal effect: all-wick core terminal rate minus all-wick outer terminal rate;
- generic outer-region strong-versus-weak wick effect;
- five-bin core and outer wick gradients;
- pair-specific interaction;
- leave-one-pair-out interaction;
- calendar-year and two-half interaction estimates;
- named-level diagnostics reported descriptively only; no selection.

## Inference

- cluster unit: pair-year;
- bootstrap draws: 5,000;
- primary two-sided p-value from clustered bootstrap sign mass;
- 95% percentile interval;
- one primary confirmatory hypothesis; no multiplicity adjustment required for the primary interaction;
- secondary diagnostics do not redefine the primary decision.

## Binding confirmation gate

`CONFIRM` only if all are true:

1. combined 2022–2025 primary interaction > 0;
2. 95% CI lower bound > 0 and bootstrap p < 0.05;
3. interaction on 2022–2023 > 0;
4. interaction on 2024–2025 > 0;
5. at least 6/10 pair interactions > 0;
6. every leave-one-pair-out pooled interaction > 0;
7. frozen core wick-bin terminal rates are non-decreasing from `<10%` through `>=40%`.

Failure of any binding gate means the exact holdout does not confirm. No threshold, pair, level or session rescue is allowed after inspection.

## Decision strings

If confirmed:

`CONFIRM_DAILY_H1_PIVOT_WICK_INTERACTION_ON_PROTECTED_HOLDOUT`

If not confirmed:

`DAILY_H1_PIVOT_WICK_INTERACTION_FAILS_PROTECTED_HOLDOUT`

If implementation/data validity fails before interpretable outcomes:

`HOLDOUT_INDETERMINATE_DATA_OR_IMPLEMENTATION_INVALID`

## What this study cannot establish

Even a holdout confirmation would establish a structural/observable association, not an executable reversal strategy. It does not define causal entry timing, stop placement, target, cost-adjusted expectancy, or live-trading readiness.
