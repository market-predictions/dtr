# Pivot Spatial-Zone Follow-up — Final Report

**Date:** 2026-08-07  
**Programme:** `PIVOT-SPATIAL-ZONE-V1`  
**Work package:** `PIV-WP-20260807-02`  
**Binding decision:** `PROMOTE_DAILY_WEEKLY_PIVOT_TERMINAL_ZONE_TO_HOLDOUT_CONFIRMATION`  
**Independent assurance:** `PASS`

## Executive conclusion

The user's concern about the original nearby placebo controls was methodologically valid enough to justify a new preregistered spatial study.

The follow-up does **not** rescue pivots as privileged broad target, stall or reversal zones. At the primary ±20% local-spacing zone, no S1–S4 target/stall/reversal mechanism passes the development/validation, confidence-interval, breadth and familywise gates.

However, a different and narrower structural effect survives: **daily and weekly pivot proximity is associated with a higher occupancy-adjusted probability that an H1 high/low becomes the terminal extreme of a confirmed ATR-defined trend leg.**

This effect:
- is positive in both 2015–2019 development and 2020–2021 validation;
- survives the preregistered 25-hypothesis Holm correction;
- is broad across pairs;
- survives leave-one-pair-out analysis;
- survives a stricter same-geometry robustness test using H1 highs/lows rather than H1 closes as exposure;
- is not dependent on a single named pivot level.

Monthly, quarterly and yearly pivot proximity does not show the same robust terminal-zone effect.

The 2022–2025 holdout remains unopened. The only justified next scientific step is a separate, frozen confirmation of the unchanged daily/weekly terminal-zone effect.

## Study design

### Pivot geometry

The classic floor-pivot formulas and NY 17:00 DST-safe period boundaries are unchanged from the parent programme.

Daily and weekly test `S3/S2/S1/PP/R1/R2/R3`. Monthly, quarterly and yearly additionally include all six arithmetic midlevels between adjacent principal pivots.

### Broad pivot zones

Five symmetric half-widths were frozen before outcomes:
- 5% of local spacing;
- 10%;
- 15%;
- **20% primary**;
- 25%.

The primary 20% pivot zone is compared with an equal-width control zone centered at the midpoint between adjacent pivots. At 20%, the real and control zones have a 10%-of-spacing gap and do not overlap.

### Mechanism tests

- **S1:** raw trend-endpoint incidence inside broad pivot zones versus midpoint-control zones.
- **S2:** qualified trend approach reaches pivot zone before adverse 0.50 ATR move versus midpoint control.
- **S3:** post-touch containment/stall, allowing sideways dwell.
- **S4:** reversal before extension after arrival, with zone dwell neutral.
- **S5:** continuous distance-gradient endpoint enrichment: terminal endpoints per H1 exposure in 0–20% of pivot spacing versus 30–50%.

Primary inference uses 5,000 pair-year-week clustered bootstrap draws and Holm correction across `S1–S5 × five timeframes = 25` hypotheses.

## Primary result

Only two positive hypotheses pass the full frozen internal gate:

| Timeframe | Test | Development | Validation | Combined | 95% CI | Holm p | Positive pairs |
|---|---|---:|---:|---:|---:|---:|---:|
| Daily | S5 terminal enrichment | +4.51 pp | +4.65 pp | **+4.55 pp** | +3.74 to +5.33 pp | <0.001 | 10/10 |
| Weekly | S5 terminal enrichment | +1.55 pp | +0.54 pp | **+1.26 pp** | +0.60 to +1.94 pp | 0.008 | 9/10 |

All leave-one-pair-out effects remain positive.

No monthly, quarterly or yearly S5 result qualifies.

## Same-geometry robustness

The preregistered S5 exposure denominator used H1 closes, while the trend-leg endpoint detector uses H1 high extrema for up legs and H1 low extrema for down legs. This construct mismatch was challenged adversarially after the primary result.

A stricter robustness test therefore compares:
- up-leg endpoints against all valid H1 highs;
- down-leg endpoints against all valid H1 lows.

The daily and weekly findings survive:

| Timeframe | Development | Validation | Combined | 95% CI (5,000 draws) | Positive pairs |
|---|---:|---:|---:|---:|---:|
| Daily | +2.21 pp | +2.31 pp | **+2.24 pp** | +1.95 to +2.52 pp | 10/10 |
| Weekly | +0.70 pp | +0.44 pp | **+0.63 pp** | +0.35 to +0.91 pp | 9/10 |
| Monthly | -0.13 pp | +0.00 pp | -0.09 pp | -0.35 to +0.16 pp | 5/10 |
| Quarterly | +0.06 pp | +0.10 pp | +0.07 pp | -0.15 to +0.30 pp | 6/10 |
| Yearly | +0.25 pp | -0.07 pp | +0.15 pp | -0.06 to +0.35 pp | 6/10 |

A separate assurance implementation with 2,000 draws and a different seed again returned intervals strictly above zero for daily and weekly.

## Spatial gradient under same-geometry robustness

### Daily

| Distance to nearest daily pivot | H1 extrema that became terminal endpoints |
|---|---:|
| 0–10% of local spacing | 32.76% |
| 10–20% | 31.98% |
| 20–30% | 31.07% |
| 30–40% | 30.16% |
| 40–50% | 30.09% |

Core 0–20% versus outer 30–50%:
- **+2.24 percentage points**
- about **+7.4% relative enrichment**

The gradient is monotonic.

### Weekly

| Distance to nearest weekly pivot | H1 extrema that became terminal endpoints |
|---|---:|
| 0–10% | 31.65% |
| 10–20% | 31.56% |
| 20–30% | 31.13% |
| 30–40% | 30.97% |
| 40–50% | 30.99% |

Core 0–20% versus outer 30–50%:
- **+0.63 percentage point**
- about **+2.0% relative enrichment**

The gradient is shallower but directionally coherent.

## Named-level dominance

The daily effect is not carried by one pivot:

- PP: +2.24 pp
- R1: +4.48 pp
- R2: +0.12 pp
- R3: -0.04 pp
- S1: +4.65 pp
- S2: -1.23 pp
- S3: +0.91 pp

Five of seven daily level families are positive, and the pooled effect stays positive after removing **any one** named level.

Weekly:
- PP: +1.02 pp
- R1: +0.34 pp
- R2: +0.67 pp
- R3: -0.29 pp
- S1: +0.56 pp
- S2: +0.23 pp
- S3: +0.59 pp

Six of seven weekly level families are positive, and every leave-one-level-out pooled effect remains positive.

This is supportive non-dominance evidence; the preregistration required non-dominance but did not prescribe a numeric leave-one-level-out criterion.

## Broad target / stall / reversal tests remain negative

The broader-zone reinterpretation does **not** support a magnet or reversal claim.

At the primary ±20% width:

| Timeframe | S2 target completion | S3 containment/stall | S4 reversal-before-extension |
|---|---:|---:|---:|
| Daily | -1.67 pp | -6.54 pp | -1.66 pp |
| Weekly | -4.09 pp | +0.81 pp | -1.61 pp |
| Monthly | -3.84 pp | +3.48 pp | -3.91 pp |
| Quarterly | +5.34 pp | 0.00 pp | +3.57 pp |
| Yearly | +0.81 pp | +9.09 pp | +9.09 pp |

None passes the frozen gate. Positive higher-timeframe values are sparse/uncertain and do not reproduce stably between development and validation.

The 5/10/15/20/25% width curves do not reveal a coherent target/stall/reversal rescue.

## Why S1 and S5 can point in opposite directions

S1 is a raw count/exposure-area comparison: broad daily/weekly pivot cores contain fewer trend endpoints than equal-width midpoint-control zones.

S5 asks a different question: **conditional on market exposure at that spatial location, how often does an H1 high/low become a terminal trend-leg extreme?**

Price also spends less H1-extrema exposure near the pivot cores. Once that lower exposure is accounted for, daily and weekly terminal-extreme probability rises toward the pivot.

The supported phenomenon is therefore a **terminal hazard / turning-point enrichment**, not raw clustering or attraction.

## Trading interpretation

This is not yet a reversal strategy.

The terminal endpoint is confirmed only after the independent ATR directional-change threshold is reached. Therefore S5 cannot be used as a causal entry signal by itself.

The justified interpretation is:

> When price is already near a daily or weekly classic pivot, an H1 high/low is modestly more likely to become the terminal extreme of the current ATR-defined directional leg than an H1 high/low occurring in the outer part of the interval between pivots.

Daily evidence is materially stronger than weekly evidence.

This may ultimately support target management, exhaustion awareness or a causal rejection/rotation trigger, but those trading rules have not been tested.

## Independent assurance

Decision: `PASS`.

Assurance independently confirmed:
- all ten canonical source archive SHA-256 identities;
- all result ledgers stop at 2021;
- exact S1–S4 point estimates from raw ledgers;
- the S5 close-based and same-geometry high/low effects;
- separately seeded 2,000-draw pair-year-week bootstrap intervals;
- daily/weekly pair breadth and leave-one-pair-out stability;
- conservative named-level leave-one-out stability.

## Scientific disposition

`PROMOTE_DAILY_WEEKLY_PIVOT_TERMINAL_ZONE_TO_HOLDOUT_CONFIRMATION`

Authorized next:
- a separate preregistered 2022–2025 confirmation of **only** the unchanged daily and weekly S5 terminal-zone mechanism.

Not authorized:
- opening holdout inside this work package;
- selecting a new spatial width;
- tuning pivot formulas, trend thresholds, barriers, sessions, pairs or named levels;
- interpreting S5 as a live reversal entry;
- execution P&L;
- Pine, alerts, sizing, paper trading or deployment.

The parent conclusion remains valid: exact pivot coordinates were not demonstrated to be privileged target or reversal lines. This follow-up adds a narrower result: daily and weekly pivots appear to define **spatial terminal zones** when measured as trend-ending hazard per market occupancy.
