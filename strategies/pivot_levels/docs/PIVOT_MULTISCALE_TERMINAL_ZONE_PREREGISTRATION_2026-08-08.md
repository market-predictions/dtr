# Pivot Multiscale Terminal-Zone Study — Preregistration

Date: 2026-08-08
Programme: `PIVOT-MULTISCALE-TERMINAL-ZONE-V1`
Study ID: `DFXC-20260808-001-pivot-multiscale-terminal`
Status at creation: `FROZEN_PRE_OUTCOME`
Parent: `DFXC-20260807-002-pivot-spatial-zone`

## Research question

Does the pivot-proximity terminal-hazard effect become more coherent when the directional-leg detector is scale-aligned to the pivot horizon rather than forcing every pivot timeframe through H1 legs?

This is an extension prompted by the parent's scale-mismatch limitation. It may not rewrite the parent's negative monthly/quarterly/yearly H1 result.

## Data contract

- Dataset: **Dukascopy FX Cash** / `dukascopy_fx_cash_m1_bid_ask_v1`.
- Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Source: registered private cache only; no historical reacquisition.
- M1 separate BID/ASK UTC; midpoint OHLC for structural measurement.
- Development: 2015-01-01 through 2019-12-31.
- Internal validation: 2020-01-01 through 2021-12-31.
- Protected holdout: 2022-01-01 through 2025-12-31, **unopened**.
- All computational loaders must hard-stop before 2022-01-01 before resampling or outcome construction.

## Frozen pivot construction

Retain the parent classic floor-pivot formulas and NY 17:00 DST-safe FX period calendar unchanged.

- Daily/weekly tested levels: S3, S2, S1, PP, R1, R2, R3.
- Monthly/quarterly/yearly: the seven principal levels plus the six adjacent arithmetic midlevels.
- Only completed prior periods generate current-period pivots.
- Normalized pivot distance uses side-specific spacing to the adjacent tested level; outer levels extrapolate the sole adjacent spacing.

## Scale alignment — primary mapping

The primary detector mapping is frozen as:

| Pivot horizon | Directional-leg / extremum timeframe |
|---|---|
| Daily | H1 |
| Weekly | H4 |
| Monthly | D1 |
| Quarterly | W1 |
| Yearly | MN1 |

Secondary scale-mismatch benchmarks retain H1 for weekly/monthly/quarterly/yearly to quantify whether scale alignment changes the result. Benchmarks cannot promote a mapping.

Resampling rules:

- H1: UTC clock-hour bars.
- H4: UTC bars aligned 00:00/04:00/08:00/12:00/16:00/20:00.
- D1: FX trading day ending 17:00 America/New_York, DST-safe.
- W1: FX week ending Friday 17:00 America/New_York.
- MN1: FX calendar month under the same FX-day labels.

## Pivot-blind ATR directional-change endpoint detector

Termination is **not** defined by pivots, wicks, volume or candle patterns.

For each detector timeframe independently:

1. Build OHLC midpoint bars using the frozen resampling rule.
2. True range is `max(H-L, abs(H-prev_close), abs(L-prev_close))`.
3. `ATR24` is the simple mean of the prior 24 completed true ranges and is lagged one detector bar.
4. Directional-change threshold at confirmation bar `t` is `0.75 * ATR24_lag1[t]`.
5. In an up leg, maintain the highest observed high and its bar. Confirm the terminal high only when a later bar close is at least the current threshold below that running high. The stored running-high bar is the terminal endpoint.
6. In a down leg, maintain the lowest observed low and its bar. Confirm the terminal low only when a later bar close is at least the current threshold above that running low. The stored running-low bar is the terminal endpoint.
7. Neutral initialization tracks running high/low until a close moves at least one current threshold away from the opposite running extreme; that opposite extreme initializes the first confirmed endpoint.
8. Missing/invalid bars break continuity and reinitialize the detector. No endpoint may bridge an unsafe gap.

The detector is retrospective by construction: an endpoint exists only after the later ATR directional change confirms it.

## Occupancy-adjusted endpoint dataset

For every detector bar inside an active pivot period:

- create one high-side observation from the bar high and one low-side observation from the bar low;
- assign each observation to its nearest tested pivot;
- normalize absolute distance by the adjacent-level spacing on the side containing the observation;
- retain normalized distances from 0% through 50%;
- mark `terminal=1` only when the corresponding bar high/low is a confirmed pivot-blind directional-leg endpoint of that side; otherwise `0`.

Distance bins are frozen at `0-10`, `10-20`, `20-30`, `30-40`, `40-50%` of local spacing.

## Primary endpoint

For each of the five scale-aligned mappings:

`terminal_rate(0-20%) - terminal_rate(30-50%)`

where rates are terminal endpoints per eligible same-geometry high/low occupancy observation.

Secondary coherence outputs:

- five-bin terminal-rate gradient;
- relative enrichment of core versus outer region;
- pair-level effects;
- leave-one-pair-out effects;
- named-level breadth/non-dominance;
- scale-aligned effect minus H1 benchmark effect for weekly/monthly/quarterly/yearly.

## Inference

- Cluster bootstrap unit: pair-year.
- 5,000 bootstrap draws for primary combined effects and confidence intervals.
- Two-sided p-values from the cluster-bootstrap null distribution.
- Holm correction across the five primary scale-aligned horizon hypotheses.
- Development and validation effects are computed separately before combined inference.

## Promotion gate

A pivot-horizon mapping survives internally only if all are true:

1. development and validation core-minus-outer effects are both positive;
2. combined 95% interval is strictly above zero;
3. Holm-adjusted two-sided p < 0.05;
4. at least 6/10 eligible pairs have positive pair-level effects;
5. every leave-one-pair-out pooled effect remains positive;
6. the five-bin profile is directionally coherent: the fitted terminal-rate slope versus distance-bin midpoint is negative;
7. no single named level is necessary for the pooled sign.

No gate is relaxed for monthly/quarterly/yearly sample scarcity.

## Interpretation boundary

A passing result means only that terminal-extreme hazard is enriched near the relevant pivot geometry at a scale-aligned leg horizon. It does not establish attraction, immediate reversal, profitable entries or causal execution.

## Restrictions

- No opening 2022-2025.
- No tuning the pivot formulas, 20% core, 30-50% outer region, ATR length, 0.75 ATR reversal threshold, scale mapping, pair universe or named levels after outcomes.
- No pair/session/year/level shopping.
- No volume, wick, P&L, Pine, alerts, sizing, paper trading or deployment inside this study.
- The separate wick/rejection study may run only under its own preregistration and only on mappings that pass this study's frozen gate.
