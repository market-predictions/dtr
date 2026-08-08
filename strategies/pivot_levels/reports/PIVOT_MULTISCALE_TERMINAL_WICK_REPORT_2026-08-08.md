# Pivot Multiscale Terminal-Zone + Wick Rejection — Final Internal Report

**Date:** 2026-08-08  
**Dataset:** Dukascopy FX Cash — ten registered FX pairs  
**Study 1:** `DFXC-20260808-001-pivot-multiscale-terminal`  
**Study 2:** `DFXC-20260808-002-pivot-wick-rejection`  
**Work package:** `PIV-WP-20260808-03`  
**Protected 2022–2025 holdout:** **UNOPENED**

## Executive conclusion

The scale-alignment hypothesis is **partly supported, not generally supported**.

- **Daily pivot → H1 directional leg** passes every frozen internal gate: combined terminal-hazard enrichment **+1.02 percentage points**, 95% CI **[+0.85, +1.20] pp**, positive in **10/10 pairs**.
- **Weekly pivot → H4 directional leg** also passes: **+0.67 pp**, 95% CI **[+0.33, +1.01] pp**, positive in **8/10 pairs**. The scale-aligned H4 effect is materially stronger than the weekly→H1 mismatch benchmark (**+0.28 pp**).
- **Monthly→D1, Quarterly→W1 and Yearly→MN1 do not pass.** The higher-timeframe scale-alignment idea therefore does **not** rescue monthly/quarterly/yearly classic pivots on the exposed 2015–2021 sample.

The conditional wick study then tested only the two structural survivors. Its most important result is narrower:

> **For daily pivots, a strong directionally appropriate H1 wick inside the pivot core carries statistically significant incremental terminal information beyond generic wick exhaustion away from pivots.**

The daily pivot-specific wick interaction is **+0.92 pp**, 95% CI **[+0.49, +1.36] pp**, with development **+1.13 pp**, validation **+0.39 pp**, positive interaction in **8/10 pairs**, and every leave-one-pair-out result positive.

Weekly→H4 wick interaction is directionally positive (**+0.77 pp**) but **fails the frozen gate** because its 95% CI crosses zero (**[-0.07, +1.59] pp**) and bootstrap p=0.0744. It is not promoted.

## Anti-circular terminal definition

Termination is not defined by a wick, pivot, volume or candle pattern. A pivot-blind ATR24 directional-change detector tracks candidate highs/lows. A candidate extreme may be confirmed only by the close of a **strictly later detector candle** after a 0.75× lagged-ATR directional change.

Same-candle confirmation is prohibited. This rule was frozen before outcomes because otherwise a large wick could mechanically help the same candle certify itself as a terminal extreme.

## Study 1 — scale-aligned terminal-zone test

Frozen mapping:

| Pivot horizon | Directional-leg / extremum horizon |
|---|---|
| Daily | H1 |
| Weekly | H4 |
| Monthly | D1 |
| Quarterly | W1 |
| Yearly | MN1 |

Primary effect is occupancy-adjusted terminal incidence in the normalized **0–20% pivot core minus 30–50% outer region**. Inference uses 5,000 pair-year clustered bootstrap draws and Holm correction across five primary mappings. Development is 2015–2019; internal validation is 2020–2021.

### Primary results

| Mapping | Development | Validation | Combined | 95% CI | Positive pairs | Gate |
|---|---:|---:|---:|---:|---:|---|
| Daily→H1 | +1.00 pp | +1.07 pp | **+1.02 pp** | +0.85 to +1.20 pp | 10/10 | **PASS** |
| Weekly→H4 | +0.73 pp | +0.52 pp | **+0.67 pp** | +0.33 to +1.01 pp | 8/10 | **PASS** |
| Monthly→D1 | +0.27 pp | -1.18 pp | -0.15 pp | -1.01 to +0.71 pp | 4/10 | FAIL |
| Quarterly→W1 | -1.18 pp | +1.33 pp | -0.43 pp | -2.06 to +1.21 pp | 3/10 | FAIL |
| Yearly→MN1 | +1.88 pp | -1.68 pp | +0.46 pp | -3.59 to +4.45 pp | 6/10 | FAIL |

For Daily→H1 and Weekly→H4, no non-positive combined effect appeared in 5,000 bootstrap draws. Both pass Holm correction, pair breadth, pair leave-one-out, negative distance-slope and named-level leave-one-out gates.

### Spatial gradients

Daily terminal incidence from nearest to farthest ten-percent bins:

`12.75% → 12.49% → 11.88% → 11.64% → 11.55%`

Weekly/H4:

`12.51% → 12.19% → 12.26% → 11.86% → 11.51%`

Daily is especially clean. Weekly is directionally coherent under the preregistered fitted-slope criterion, though not perfectly monotonic bin-by-bin.

### Pair breadth

Daily→H1 is positive in all ten pairs, from approximately +0.58 pp (EURGBP) to +1.44 pp (GBPUSD/USDCAD). Every pair leave-one-out and every named-level leave-one-out pooled effect remains positive.

Weekly→H4 is positive in eight pairs. AUDUSD (-0.39 pp) and USDCHF (-0.09 pp) are negative, but every leave-one-pair-out pooled effect remains positive; no named pivot family is necessary for the pooled sign.

### Scale alignment versus H1 mismatch

| Pivot | Scale-aligned | H1 benchmark | Conclusion |
|---|---:|---:|---|
| Weekly | **+0.67 pp (H4)** | +0.28 pp | Alignment strengthens effect |
| Monthly | -0.15 pp (D1) | -0.09 pp | No rescue |
| Quarterly | -0.43 pp (W1) | +0.02 pp | No rescue |
| Yearly | +0.46 pp (MN1) | ~0.00 pp | Unstable / sparse |

This rejects a universal fractal pivot claim. Scale appears relevant for weekly pivots, but moving to D1/W1/MN1 does not make monthly/quarterly/yearly pivots robust terminal zones.

## Study 2 — wick rejection as observable exhaustion information

Only Daily→H1 and Weekly→H4 were eligible. Directional wick fraction was frozen as:

- high-side: `(H - max(O,C)) / (H-L)`;
- low-side: `(min(O,C) - L) / (H-L)`.

Strong rejection is wick ≥30% of candle range; weak rejection is <10%. The primary endpoint is:

`(core strong − core weak) − (outer strong − outer weak)`

This asks whether wick rejection contains **more** terminal information near a pivot than it contains generically elsewhere.

### Daily→H1 — PASS

| Cell | Terminal probability |
|---|---:|
| Pivot core + strong wick | **17.67%** |
| Pivot core + weak wick | 7.20% |
| Outer region + strong wick | 16.04% |
| Outer region + weak wick | 6.50% |

Therefore:

- generic outer-region strong-vs-weak wick effect: **+9.55 pp**;
- pivot-core strong-vs-weak wick effect: **+10.47 pp**;
- incremental pivot-zone interaction: **+0.92 pp**, 95% CI **[+0.49, +1.36] pp**.

The core terminal-rate gradient across the frozen directional-wick bins is monotonic:

`7.20% → 9.53% → 11.88% → 14.13% → 19.43%`

for `<10%`, `10–20%`, `20–30%`, `30–40%`, `≥40%` wick fractions.

This is an important distinction: **wicks themselves are a strong generic exhaustion signature.** Pivot proximity adds a smaller but statistically defensible extra layer. The result is not “pivots cause wicks”; it is “the same rejection geometry carries modestly more terminal information in the daily pivot core.”

Daily pivot-specific wick interaction is positive in eight pairs. EURJPY and GBPJPY are effectively flat/slightly negative, while every pooled leave-one-pair-out interaction remains positive.

### Weekly→H4 — FAIL, no rescue

Weekly/H4 also has a large generic wick effect and a positive point-estimate interaction, but the pivot-specific increment is not sufficiently certain:

- interaction **+0.77 pp**;
- 95% CI **[-0.07, +1.59] pp**;
- bootstrap p=0.0744;
- 9/10 pairs positive, with GBPJPY materially negative.

The frozen gate therefore fails. No wick-threshold tuning, pair removal or level selection is authorized to rescue it.

## Strategic interpretation

The evidence now supports a narrower architecture than the original classic-pivot thesis:

1. **Daily classic pivots define a modest but robust H1 terminal-hazard zone.**
2. **Weekly pivots define a weaker but robust H4 terminal-hazard zone.**
3. **Monthly, quarterly and yearly pivots remain unsupported as analogous terminal zones even after scale alignment.**
4. **Strong directional wicks are powerful generic exhaustion information.**
5. **For daily pivots only, wick rejection receives an additional pivot-proximity premium that survives the frozen internal gates.**

This is not yet a trading entry. Endpoint identity remains retrospective, and transaction costs, trigger timing, stop logic, confirmation delay and lower-timeframe execution have not been tested.

## Validation completed

- All 22 registered split source parts passed their canonical SHA-256 checks.
- Every reconstructed pair archive passed its registered full-archive SHA-256 before analysis.
- Only annual BID/ASK members for 2015–2021 were opened; result ledgers contain years 2015–2021 only.
- Ten pairs × nine mappings are present with no missing pair/mapping cell.
- A separate arithmetic implementation recomputed all five Study-1 combined core-minus-outer effects and both eligible Study-2 interactions exactly from the aggregated counts.
- A synthetic anti-circularity unit check confirmed that a large-wick candidate extreme cannot self-confirm and is marked terminal only after a later detector bar satisfies the ATR reversal criterion.

These checks are implementation validation, not independent `governance_release_assurance`.

## Next scientific gate

The strongest candidate for protected confirmation is the **unchanged Daily pivot → H1 wick-rejection interaction**:

- same classic daily pivots;
- same normalized 0–20% core and 30–50% outer region;
- same H1 ATR24 / 0.75 directional-change endpoint definition;
- same strictly-later confirmation rule;
- same wick bins and ≥30% strong / <10% weak contrast;
- same ten pairs;
- no pair, named-level, session or threshold selection.

The 2022–2025 protected holdout remains unopened and available for that confirmation after independent assurance of the implementation candidate and the applicable holdout authorization.

Weekly/H4 structural proximity may remain a separate structural holdout candidate, but its wick interaction is classified as failed internally unless tested on fresh independent data later.

## Limitations

- Yearly→MN1 is severely sample-limited because ATR24 on monthly bars requires a two-year warm-up; no gate was relaxed for this scarcity.
- Structural midpoint prices were used; this is not executable BID/ASK P&L research.
- Endpoint identity is retrospective even though wick geometry is observable at candle close.
- The daily wick interaction is a conditional internal mechanism result because eligibility was selected on the same exposed 2015–2021 sample; protected/fresh data are required for independent confirmation.
- No centralized FX volume is used. Tick/activity-volume confirmation remains a later research question.

## Binding implementation disposition

- Study 1: `PROMOTE_DAILY_H1_AND_WEEKLY_H4_TERMINAL_ZONES_REJECT_HIGHER_TF_SCALE_RESCUE`.
- Study 2: `PROMOTE_DAILY_PIVOT_WICK_INTERACTION_WEEKLY_FAILS_GATE`.
- Holdout: `UNOPENED`.
- Live trading / Pine / alerts / sizing: `NOT_AUTHORIZED_BY_THIS_RESEARCH`.
