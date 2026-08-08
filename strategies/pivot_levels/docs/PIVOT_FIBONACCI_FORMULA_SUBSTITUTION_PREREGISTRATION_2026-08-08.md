# Preregistration — Fibonacci Pivot Formula Substitution

Date: 2026-08-08
Study ID: `DFXC-20260808-005-pivot-fibonacci-substitution`
Parents: `DFXC-20260808-003-pivot-daily-wick-holdout`, `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`
Dataset: **Dukascopy FX Cash**
Study type: robustness / formula-substitution falsification

## Question

If the successful Daily→H1 and Weekly→H4 pivot/wick tests are repeated with standard Fibonacci-calculated pivot levels while preserving every other successful design choice, does the terminal-zone / directional-wick relationship remain supported, strengthen, or degrade relative to classic floor pivots?

The purpose is formula substitution only. Zone width, response timeframe, terminal definition, wick thresholds, pair universe, and sample partition are not retuned.

## Data boundary

Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.

Development: 2015–2019.
Internal validation: 2020–2021.

No 2022–2025 result is used as a pristine holdout for this new Fibonacci hypothesis. Those years have already been exposed for the related Daily/H1 classic-pivot programme. The primary study therefore remains on 2015–2021 only. No 2026 outcome is inspected in this study.

Price basis: midpoint structural OHLC from synchronized Dukascopy BID/ASK M1.
FX pivot periods: NY17 DST-safe daily and weekly periods.
Response bars: H1 for Daily pivots; UTC-aligned H4 for Weekly pivots.

## Fibonacci pivot construction — frozen

For the prior completed pivot period, let `R = H - L` and:

`PP = (H + L + C) / 3`

Standard Fibonacci pivot coordinates:

- `R1 = PP + 0.382 * R`
- `R2 = PP + 0.618 * R`
- `R3 = PP + 1.000 * R`
- `S1 = PP - 0.382 * R`
- `S2 = PP - 0.618 * R`
- `S3 = PP - 1.000 * R`

Tested levels: S3, S2, S1, PP, R1, R2, R3. No named-level selection.

The classic comparator is recalculated in the same engine from the same prior-period H/L/C:

- `PP = (H+L+C)/3`
- `R1 = 2*PP-L`, `S1 = 2*PP-H`
- `R2 = PP+(H-L)`, `S2 = PP-(H-L)`
- `R3 = H+2*(PP-L)`, `S3 = L-2*(H-PP)`

## Frozen Daily→H1 geometry

The successful Daily/H1 geometry is preserved unchanged:

1. assign each H1 high/low to the nearest current Fibonacci daily pivot;
2. define `local_spacing` as distance to the adjacent tested Fibonacci pivot in the observation direction; outer S3/R3 use inward spacing;
3. normalized distance `d = abs(extreme-pivot)/local_spacing`;
4. core `0 <= d < 0.20`;
5. outer control `0.30 <= d <= 0.50`.

The classic comparator uses the same normalized 0–20% / 30–50% geometry around classic pivot coordinates.

## Frozen Weekly→H4 geometry

The successful Weekly/H4 geometry is preserved unchanged at `SP10`:

1. assign each H4 high/low to the nearest current Fibonacci weekly pivot;
2. local spacing uses adjacent Fibonacci weekly-pivot distance in observation direction;
3. normalized distance `d = abs(extreme-pivot)/local_spacing`;
4. core `0 <= d < 0.10`;
5. equal-width outer control `0.40 <= d <= 0.50`.

The classic comparator uses the same SP10 geometry around classic weekly pivots.

No 5%, 7.5%, 12.5%, ATR cap, or other geometry is tested.

## Terminal definition — unchanged and pivot-blind

For each response timeframe separately:

- true range from H/L/prior close;
- ATR24 simple mean, shifted one response bar;
- directional-change threshold `0.75 * ATR24_lag1`;
- candidate high/low extrema tracked without pivot or wick information;
- candidate extreme can become terminal only after a strictly later response candle closes at least the threshold in the opposite direction;
- same-candle confirmation prohibited.

## Directional wick definition — unchanged

High-side wick fraction: `(H-max(O,C))/(H-L)`.
Low-side wick fraction: `(min(O,C)-L)/(H-L)`.

Frozen bins: `<10%`, `10–20%`, `20–30%`, `30–40%`, `>=40%`.
Strong = `>=30%`.
Weak = `<10%`.

## Endpoints

For each horizon/formula:

### Structural endpoint

`terminal_effect = core_terminal_rate - outer_terminal_rate`

### Primary wick endpoint

`wick_interaction = (core_strong - core_weak) - (outer_strong - outer_weak)`

### Formula-difference endpoint

For each horizon, compute the pair-year clustered difference:

`delta_formula = Fibonacci effect - Classic effect`

for both structural and wick endpoints.

This directly tests whether changing only the pivot formula improves or degrades the established effect. A positive Fibonacci effect is not automatically interpreted as superiority over classic pivots.

## Inference

- 5,000 pair-year clustered bootstrap draws;
- development, validation and combined estimates;
- 95% percentile confidence interval;
- pair-specific effects;
- leave-one-pair-out pooled effects;
- five-bin core wick gradient;
- paired Fibonacci-minus-Classic effect distribution by pair-year cluster.

Multiplicity:

- Holm correction across two Fibonacci structural hypotheses: Daily/H1 and Weekly/H4;
- separate Holm correction across two Fibonacci wick hypotheses.

Formula-difference intervals are descriptive/confirmatory comparisons and do not create additional candidate selection.

## Support gate

A Fibonacci horizon is `SUPPORTED_INTERNAL` only if both its structural and wick endpoints satisfy:

1. development > 0;
2. validation > 0;
3. combined > 0;
4. 95% CI lower bound > 0;
5. Holm-adjusted p < 0.05;
6. at least 6/10 pair effects > 0;
7. every leave-one-pair-out pooled effect > 0;
8. core wick-bin terminal rates are non-decreasing.

## Formula interpretation

For a supported Fibonacci horizon:

- `FIBONACCI_STRONGER` if the paired Fibonacci-minus-Classic wick-interaction 95% CI lower bound > 0;
- `CLASSIC_STRONGER` if its 95% CI upper bound < 0;
- `FORMULA_EQUIVALENT_WITHIN_UNCERTAINTY` otherwise.

The structural delta is reported alongside but does not override the wick formula comparison.

If Fibonacci fails its own support gate, decision is `FIBONACCI_FORMULA_NOT_SUPPORTED_FOR_<HORIZON>` regardless of point-estimate comparison.

## Prohibited rescue

After outcomes are inspected, do not:

- substitute alternative Fibonacci coefficients such as 0.236, 0.786, 1.272 or 1.618;
- change Daily 20% or Weekly 10% zone widths;
- add ATR-adjusted zones;
- tune wick thresholds;
- select currency pairs;
- select PP/R1/S1 or any named level;
- add session filters;
- use 2022–2025 to choose between formulas.

Any such question requires a new preregistered study and new evidence.

## What this study cannot establish

Even a positive Fibonacci result is a structural/exhaustion association, not a trading strategy. It does not establish entries, stops, targets, transaction-cost-adjusted expectancy, Pine readiness, or live-trading authority.
