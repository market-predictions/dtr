# Preregistration — Weekly Pivot × H4 Zone Geometry Robustness

Date: 2026-08-08
Study ID: `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`
Parents: `DFXC-20260808-001-pivot-multiscale-terminal`, `DFXC-20260808-002-pivot-wick-rejection`
Dataset: **Dukascopy FX Cash**
Study type: robustness / falsification

## Question

The Weekly→H4 structural terminal-zone effect passed internally, while the Weekly→H4 pivot-specific wick interaction was +0.77 pp but failed its frozen significance gate. Is the weak interaction partly caused by a pivot-zone definition that scales only with weekly pivot spacing and ignores normal H4 price noise?

## Existing reference geometry

For each H4 high or low, the parent study assigns the nearest current weekly classic pivot from S3/S2/S1/PP/R1/R2/R3. `local_spacing` is the adjacent tested-pivot distance in the direction of the observation; at outer levels the corresponding inward spacing is used.

Normalized distance:

`d = abs(extreme - pivot) / local_spacing`

Reference:

- core: `0 <= d < 0.20`
- outer: `0.30 <= d <= 0.50`

This is **purely relative to adjacent weekly-pivot spacing**. ATR is used only in the independent terminal detector, not in the zone width.

## Mechanism motivating this robustness test

A fixed fraction of weekly pivot spacing can represent very different amounts of ordinary H4 volatility. When a prior week is unusually wide, 20% of pivot spacing may be several normal H4 noise units and dilute a localized response. When spacing is tight, the same fraction may already be narrow. A volatility-aware cap could therefore improve the signal-to-noise ratio without abandoning structural pivot spacing.

The test is deliberately limited to interpretable geometries and does not tune wick thresholds, pairs, pivot levels or sessions.

## Data boundary

Development: 2015–2019.
Internal validation: 2020–2021.

No 2022–2025 Weekly/H4 outcome is permitted in this study. The fact that 2022–2025 may be consumed separately for an authorized Daily/H1 holdout does not authorize weekly inspection.

Price basis: midpoint structural OHLC.
H4 bars: UTC-aligned four-hour bars as in the parent scale-aligned study.
FX pivot periods: NY17 DST-safe weekly periods ending Friday.

## Terminal definition — unchanged

H4 terminal labels use the same pivot-blind ATR directional-change algorithm as the parent:

- simple ATR24;
- shifted one H4 bar;
- threshold `0.75 * ATR24_lag1`;
- candidate extreme confirmable only on a strictly later H4 candle.

## Directional wick definition — unchanged

High-side wick fraction: `(H-max(O,C))/(H-L)`.
Low-side wick fraction: `(min(O,C)-L)/(H-L)`.

Strong `>=30%`; weak `<10%`. Five bins remain `<10`, `10–20`, `20–30`, `30–40`, `>=40%`.

## Frozen zone family

Let:

- `S = local_spacing` to the adjacent tested weekly pivot on the observation side;
- `A = H4_ATR24_lag1` for the observation candle;
- `w` = absolute core half-width around the nearest pivot;
- nearest-pivot corridor ends at `0.50*S`.

For every variant, the control band has the **same absolute width `w`** and sits at the far edge of the nearest-pivot corridor:

- core: `distance < w`;
- outer matched control: `0.50*S - w <= distance <= 0.50*S`.

This makes the inherited 20% reference exactly equivalent to core 0–20% versus outer 30–50% while allowing narrower geometries to retain equal-width controls.

Seven variants:

1. `SP10`: `w = 0.10*S`.
2. `SP15`: `w = 0.15*S`.
3. `SP20_REF`: `w = 0.20*S`.
4. `SP25`: `w = 0.25*S`.
5. `HYB_ATR050`: `w = min(0.20*S, 0.50*A)`.
6. `HYB_ATR075`: `w = min(0.20*S, 0.75*A)`.
7. `HYB_ATR100`: `w = min(0.20*S, 1.00*A)`.

Hybrid variants can narrow the 20%-spacing reference when normal H4 volatility is small relative to the weekly pivot corridor, but cannot widen beyond 20% of spacing. `SP25` is the one preregistered broader structural alternative. No other widths may be added after outcome inspection.

## Endpoints

### Structural endpoint

`terminal_effect = core_terminal_rate - matched_outer_terminal_rate`

using all eligible H4 high/low observations.

### Primary wick endpoint

`wick_interaction = (core_strong - core_weak) - (outer_strong - outer_weak)`

where each cell is terminal probability.

## Inference

For each of the seven geometries:

- 5,000 pair-year clustered bootstrap draws;
- development, validation and combined point estimates;
- 95% percentile CI;
- pair-specific effects;
- leave-one-pair-out pooled effects;
- five-bin core wick gradient;
- distribution of effective core half-width as a fraction of spacing and as ATR units.

Multiplicity:

- Holm correction across seven structural hypotheses;
- separate Holm correction across seven wick-interaction hypotheses.

## Promotion gate for a weekly geometry

A geometry is an internally supported weekly zone only if both structural and wick endpoints satisfy:

1. development > 0;
2. validation > 0;
3. combined > 0;
4. 95% CI lower bound > 0;
5. Holm-adjusted p < 0.05;
6. at least 6/10 pair effects > 0;
7. every leave-one-pair-out pooled effect > 0.

For the wick endpoint the frozen five-bin core wick terminal rates must additionally be non-decreasing.

## Material-strength classification

A passing weekly wick geometry is called **materially stronger than `SP20_REF`** only if:

- combined interaction >= +1.00 pp; and
- combined interaction exceeds the `SP20_REF` interaction by at least +0.25 pp.

This label is descriptive; passing the inferential gates is still required.

## Selection discipline

All seven variants will be reported. No failed variant is hidden. If multiple geometries pass, no pair or pivot-level subset will be used to break ties. The simplest geometry that remains statistically and temporally robust will be preferred for any future preregistration; any future confirmation requires a new frozen study before fresh/unseen weekly data.

## Prohibited rescue

After outcomes are inspected, do not:

- add 5%, 12.5%, 17.5%, 30% or other spacing widths;
- add ATR coefficients outside 0.50/0.75/1.00;
- switch from `min` to `max` hybrid geometry;
- tune strong/weak wick thresholds;
- remove GBPJPY or any other pair;
- select PP/S1/R1 or other named levels;
- add session filters;
- use 2022–2025 weekly results to choose a geometry.

Any such question would require a new study and fresh evidence.

## Decision interpretation

This is not a strategy test. A positive result would mean that the definition of weekly pivot proximity matters for H4 terminal/wick association. It would still not establish entry timing, reversal expectancy, stop/target logic or executable profitability.
