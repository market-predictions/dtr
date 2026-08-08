# Daily/H1 Protected Holdout + Weekly/H4 Zone Geometry — Final Internal Report

**Date:** 2026-08-08  
**Dataset:** Dukascopy FX Cash — ten registered FX pairs  
**Study 3:** `DFXC-20260808-003-pivot-daily-wick-holdout`  
**Study 4:** `DFXC-20260808-004-pivot-weekly-h4-zone-geometry`  
**Work package:** `PIV-WP-20260808-04`

## Executive conclusion

Two distinct questions were tested under separate data boundaries.

1. The **unchanged Daily classic-pivot × H1 wick interaction confirms on the protected 2022–2025 holdout**. The interaction is **+1.08 percentage points**, 95% CI **[+0.65, +1.54] pp**, is positive in **10/10 pairs**, positive in every year 2022–2025 and both preregistered two-year halves, and remains positive under every leave-one-pair-out calculation. The frozen five-bin core wick gradient remains monotonic. Binding decision: `CONFIRM_DAILY_H1_PIVOT_WICK_INTERACTION_ON_PROTECTED_HOLDOUT`.
2. The user's concern about the Weekly/H4 zone definition was valid. The inherited zone was **purely spacing-relative**, not ATR-based: core 0–20% of adjacent weekly-pivot spacing versus outer 30–50%. Under the preregistered seven-geometry robustness family, only a **narrow 0–10% spacing zone (`SP10`)** passes the joint structural + wick gates after Holm correction. Its weekly wick interaction rises from **+0.77 pp** at the inherited 20% reference to **+1.62 pp**, 95% CI **[+0.52, +2.69] pp**. The three ATR-capped hybrids do not pass the wick gate.

The resulting interpretation is narrower and stronger than “weekly pivots need an ATR zone”: **Weekly/H4 pivot response is highly local to the pivot coordinate. A 20% spacing zone diluted the wick interaction; a 10% spacing zone isolates it. ATR capping did not improve on the simplest narrow spacing geometry.**

## 1. What a pivot zone means in this programme

Classic floor pivots are calculated from the prior completed NY17 period. For weekly tests the tested coordinates are `S3, S2, S1, PP, R1, R2, R3`.

For every H4 high or low observation:

1. assign the nearest current weekly pivot;
2. determine `local_spacing` to the adjacent tested pivot in the direction of the observation;
3. compute normalized distance `d = abs(extreme - pivot) / local_spacing`.

The prior reference was:

- **core:** `0 <= d < 0.20`;
- **outer control:** `0.30 <= d <= 0.50`.

So a “20% zone” is not 20% of ATR and not a fixed pip distance. It is 20% of the local distance between neighboring pivot coordinates. Because local pivot spacing inherits the prior week's range, the absolute width expands and contracts with that range.

ATR24 is separate: it is lagged one H4 candle and defines the pivot-blind 0.75×ATR directional-change threshold used to confirm whether an H4 extreme eventually became terminal. A candidate extreme can only be confirmed on a strictly later H4 candle.

## 2. Why a weekly geometry robustness test was justified

At the inherited 20% width, the median weekly half-zone was approximately **0.62 H4 ATR**; the 10th–90th percentile was approximately **0.39–1.03 H4 ATR**. Thus the same “20% of pivot spacing” sometimes covered less than half an H4 ATR and sometimes more than one H4 ATR.

That creates a plausible dilution mechanism: in high-range weeks the structural 20% zone can encompass a substantial amount of ordinary H4 price noise. The preregistration therefore tested fixed spacing widths 10%, 15%, 20%, 25% and three hybrids that could **narrow** the 20% reference to 0.50, 0.75 or 1.00 lagged H4 ATR while never widening beyond 20% of pivot spacing.

Every geometry used an **equal absolute-width control band** at the far edge of the nearest-pivot corridor. For example:

- SP10: core 0–10%; outer 40–50%;
- SP15: core 0–15%; outer 35–50%;
- SP20 reference: core 0–20%; outer 30–50%;
- SP25: core 0–25%; outer 25–50%.

This prevents a narrow core from being compared with a much wider control region.

## 3. Daily/H1 protected holdout — CONFIRMED

The 2022–2025 holdout was opened only after the exact parent specification and authorization were committed. 2021 was used only for warm-up/prior-day pivot construction and contributes no outcome observation; 2026 was not read.

Primary interaction:

`(core strong wick − core weak wick) − (outer strong wick − outer weak wick)`

### Holdout cells

| Cell | Terminal probability | Terminal / observations |
|---|---:|---:|
| Daily pivot core + strong H1 wick | 17.38% | 12,739 / 73,296 |
| Daily pivot core + weak H1 wick | 6.63% | 2,888 / 43,563 |
| Outer region + strong H1 wick | 15.89% | 13,242 / 83,336 |
| Outer region + weak H1 wick | 6.22% | 3,143 / 50,501 |

- core strong-minus-weak: **+10.75 pp**;
- generic outer strong-minus-weak: **+9.67 pp**;
- pivot-specific incremental interaction: **+1.08 pp**, 95% CI **[+0.65, +1.54] pp**;
- structural all-wick core-minus-outer effect: **+0.89 pp**, 95% CI **[+0.68, +1.10] pp**.

No non-positive primary interaction occurred among the 5,000 clustered bootstrap draws; the machine result therefore records empirical p=0.0. This should be read as “0/5,000 non-positive draws,” not as a claim of a mathematical p-value of exactly zero.

### Temporal stability

- 2022: **+1.12 pp**
- 2023: **+0.98 pp**
- 2024: **+0.79 pp**
- 2025: **+1.40 pp**
- 2022–2023: **+1.05 pp**
- 2024–2025: **+1.11 pp**

Pair breadth is **10/10 positive**. Every pooled leave-one-pair-out interaction remains positive, with the weakest leave-one-out pooled estimate still approximately **+0.94 pp**.

### Wick-severity gradient

Core terminal rates by frozen directional-wick bin:

`6.63% → 9.13% → 11.53% → 14.14% → 18.98%`

for `<10%`, `10–20%`, `20–30%`, `30–40%`, `>=40%`. The monotonicity gate passes.

### Scientific disposition

The Daily/H1 interaction is no longer merely an internal 2015–2021 candidate. It **survived its preregistered protected 2022–2025 confirmation**. The holdout is now consumed for this exact question. This still does not establish an executable reversal strategy.

## 4. Weekly/H4 zone geometry — the 10% zone wins

All seven geometries were evaluated on 2015–2021 only with 5,000 pair-year clustered bootstrap draws. Structural effects and wick interactions had separate Holm seven-hypothesis families.

| Geometry | Structural effect | Structural 95% CI | Wick interaction | Wick 95% CI | Wick Holm p | Joint gate |
|---|---:|---:|---:|---:|---:|---|
| SP10 | +1.00 pp | [+0.48, +1.53] pp | +1.62 pp | [+0.52, +2.69] pp | 0.0308 | PASS |
| SP15 | +0.72 pp | [+0.32, +1.13] pp | +0.97 pp | [-0.01, +1.94] pp | 0.3120 | FAIL |
| SP20_REF | +0.67 pp | [+0.34, +1.01] pp | +0.77 pp | [-0.04, +1.61] pp | 0.3180 | FAIL |
| SP25 | +0.53 pp | [+0.24, +0.84] pp | +0.54 pp | [-0.22, +1.28] pp | 0.3504 | FAIL |
| HYB_ATR050 | +0.50 pp | [+0.11, +0.90] pp | +0.58 pp | [-0.43, +1.60] pp | 0.3504 | FAIL |
| HYB_ATR075 | +0.63 pp | [+0.28, +1.00] pp | +0.67 pp | [-0.17, +1.50] pp | 0.3504 | FAIL |
| HYB_ATR100 | +0.65 pp | [+0.31, +0.99] pp | +0.71 pp | [-0.12, +1.54] pp | 0.3504 | FAIL |

Only **SP10** passes the complete joint gate.

### SP10 details

- half-width: **10% of adjacent weekly pivot spacing**;
- matched outer control: **40–50% of spacing**;
- median half-width: **0.31 H4 ATR**;
- 10th–90th percentile width: **0.20–0.51 H4 ATR**.

Structural terminal effect:

- development: **+1.15 pp**;
- validation: **+0.65 pp**;
- combined: **+1.00 pp**;
- 95% CI: **[+0.48, +1.53] pp**;
- Holm p: **0.0016**;
- 8/10 pair structural effects positive;
- every leave-one-pair-out structural effect positive.

Pivot-specific wick interaction:

- development: **+1.69 pp**;
- validation: **+1.44 pp**;
- combined: **+1.62 pp**;
- 95% CI: **[+0.52, +2.69] pp**;
- raw p: **0.0044**;
- Holm p: **0.0308**;
- 9/10 pair interactions positive;
- every leave-one-pair-out wick interaction positive;
- frozen five-bin core wick gradient remains non-decreasing.

It therefore satisfies the preregistered “materially stronger” label: >=+1.00 pp and at least +0.25 pp above SP20_REF.

### Why this is materially different from SP20

The inherited 20% reference reproduces exactly:

- structural **+0.67 pp**;
- wick interaction **+0.77 pp**, CI crossing zero.

SP10 produces:

- structural **+1.00 pp**;
- wick interaction **+1.62 pp**.

The wick interaction therefore more than doubles while the structural terminal effect rises by roughly 50%.

## 5. What the ATR hybrids tell us

The ATR hypothesis was reasonable but is not what the data support in this frozen family.

- `HYB_ATR050` caps the 20% zone at 0.50 H4 ATR and binds on about **71.7%** of observations. Wick interaction: **+0.58 pp**, fail.
- `HYB_ATR075` binds on about **31.4%**. Wick interaction: **+0.67 pp**, fail.
- `HYB_ATR100` binds on about **11.3%**. Wick interaction: **+0.71 pp**, fail.

Thus a volatility cap is not required to explain the stronger weekly relationship. The simplest supported description is **a very local pivot neighborhood measured relative to the adjacent weekly pivot structure**.

## 6. Descriptive distance decomposition

A post-decision descriptive decomposition—not used for selection—helps explain SP10. Weekly all-wick terminal probability by 10%-spacing bin is approximately:

`12.51% → 12.19% → 12.26% → 11.86% → 11.51%`.

The generic strong-minus-weak wick effect by the same bins is approximately:

`11.34 pp → 10.07 pp → 10.14 pp → 10.12 pp → 9.72 pp`.

So the SP10 result is not solely an artifact of choosing the farthest 40–50% control. The **0–10% core itself has stronger wick exhaustion than the adjacent 10–20% bin** by about +1.27 pp descriptively. Moving the equal-width control farther out increases the full difference-in-differences to the preregistered +1.62 pp.

This decomposition is exploratory and does not authorize further 5%, 7.5%, 12.5% or other tuning on the same sample.

## 7. Reproducibility and invalidated preliminary runs

The weekly study had an explicit deterministic reference-reproduction gate. Two preliminary weekly challenger calculations were therefore invalidated before scientific acceptance:

1. an M1-filter/H4-aggregation ordering difference caused a tiny SP20 mismatch;
2. after correcting that, four non-terminal observations exactly on the 20% boundary differed because `distance < 0.20*spacing` and parent `distance/spacing < 0.20` can resolve differently at floating precision.

Both issues are recorded in dedicated implementation-deviation documents. After restoring the parent's normalized-distance boundary semantics, `SP20_REF` reproduced the parent combined structural and wick effects **exactly to floating-point precision**. Only that final run is admissible.

Independent arithmetic validation from the compact pair ledgers separately recomputed:

- Daily holdout interaction and structural effect;
- SP10 structural and wick effects;
- SP20 reference structural and wick effects;
- exact outcome-year boundaries;
- ten-pair universes.

Validation status: **PASS**.

## 8. Strategic interpretation

The evidence now supports two different maturity levels:

### Daily pivot → H1

The structural/wick phenomenon has passed both internal 2015–2021 research and a preregistered protected 2022–2025 holdout. A strong H1 directional rejection wick is powerful generic exhaustion information, and Daily pivot-core proximity adds a smaller incremental premium that has now replicated on untouched data.

This is mature enough to justify a new causal/execution research phase, but not direct live trading.

### Weekly pivot → H4

The parent 20% zone was not the best representation of the weekly relationship. The evidence favors a **10%-of-adjacent-pivot-spacing core**. This is an internally selected robustness result on 2015–2021, not a protected weekly confirmation. It must be frozen unchanged before any fresh weekly confirmation.

## 9. Next authorized scientific questions

- Daily/H1: design a new causal trade-recognition study around observable H1 wick close, subsequent confirmation, invalidation/stop geometry and realistic BID/ASK execution. The confirmed structural result itself must not be retuned.
- Weekly/H4: freeze `SP10` unchanged for future confirmation. The cleanest evidence is genuinely fresh data after the existing cache end, because 2022–2025 has now been viewed for the separate Daily/H1 question even though Weekly/H4 outcomes were not inspected in this study.

No further weekly width/ATR optimization on 2015–2021 is authorized by this programme.

## Limitations

- The holdout and weekly studies are structural midpoint analyses, not executable P&L tests.
- Terminal identity remains retrospective even though wick geometry is observable at candle close.
- SP10 was selected within a preregistered seven-geometry family and corrected for that family, but still requires independent weekly confirmation.
- The daily holdout consumes 2022–2025 for the Daily/H1 question. It does not make that period pristine for every future related pivot hypothesis, even though Weekly/H4 outcomes were intentionally not inspected.
- OTC Dukascopy FX Cash is a single-provider cash-FX quote source, not a consolidated order book.

## Binding implementation decisions

- `DFXC-20260808-003`: `CONFIRM_DAILY_H1_PIVOT_WICK_INTERACTION_ON_PROTECTED_HOLDOUT`.
- `DFXC-20260808-004`: `WEEKLY_H4_ZONE_GEOMETRY_MATERIALLY_STRENGTHENS_PIVOT_WICK_INTERACTION`.
- Daily/H1 2022–2025 exact-question holdout: `OPENED_AND_CONSUMED`.
- Weekly/H4 2022–2025 outcomes in this study: `NOT_INSPECTED`.
- Live trading / Pine / alerts / sizing: `NOT_AUTHORIZED_BY_THIS_RESEARCH`.
- Independent governance assurance: `PENDING`.
