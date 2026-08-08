# Daily/H1 Classic Pivot × Wick — Named-Level Decomposition

**Date:** 2026-08-08  
**Study:** `DFXC-20260808-006-pivot-daily-level-decomposition`  
**Dataset:** Dukascopy FX Cash — ten registered FX pairs  
**Outcome window:** consumed Daily/H1 holdout, 2022–2025  
**Study type:** diagnostic reconstruction; no level-selection authorization

## Executive conclusion

First-order daily pivots **S1/R1 carry the materially useful pivot-specific H1 wick interaction** in the reconstructed holdout diagnostics. The pooled S1/R1 interaction is **+2.39 pp**, versus only **+0.20 pp** for S2/R2. The preregistered-before-inspection tier contrast is therefore **+2.19 pp**; a 5,000-draw pair-year clustered bootstrap on the reference reconstruction gives 95% CI **[+0.35,+3.96] pp** and a two-sided sign-mass p≈**0.0176**. The contrast is positive in **9/10 pairs** and **4/4 years**. PP remains positive at **+1.25 pp**; S3/R3 pooled is negative at **−0.92 pp**.

This is a strong mechanistic diagnostic, but not a new protected-holdout confirmation. The original 2022–2025 holdout is already consumed, and the original heavy terminal ledger was intentionally not retained. The current reconstruction reproduces the **entire observation geometry exactly**—491,589 observations and every frozen core/outer × strong/weak denominator—but does not reproduce terminal labels exactly. Its pooled interaction is +1.124 pp versus the frozen +1.084 pp (residual +0.040 pp), while retained terminal count is 62,143 versus 57,863. Therefore the named-level numbers below must be read as **reconstructed diagnostics**, with the tier ranking strengthened by sensitivity analysis rather than represented as exact replay.

## 1. Exact population reconstruction

The following quantities match the frozen holdout exactly:

| Quantity | Reconstructed | Frozen |
|---|---:|---:|
| Retained observations (`d <= 0.50`) | 491,589 | 491,589 |
| Core + strong wick observations | 73,296 | 73,296 |
| Core + weak wick observations | 43,563 | 43,563 |
| Outer + strong wick observations | 83,336 | 83,336 |
| Outer + weak wick observations | 50,501 | 50,501 |

This exact match validates the cache restoration, midpoint H1 bars, NY17 daily pivots, nearest-level assignment, side-specific spacing, normalized-distance zones and wick classification.

## 2. Named-level results

| Level | Pivot-specific wick interaction | Core strong terminal | Core weak terminal | Outer strong | Outer weak | Strong proximity premium | Weak proximity premium |
|---|---:|---:|---:|---:|---:|---:|---:|
| S3 | **-2.33 pp** | 22.82% | 10.09% | 24.95% | 9.89% | -2.13 pp | +0.20 pp |
| S2 | **-0.29 pp** | 24.74% | 8.56% | 24.92% | 8.46% | -0.18 pp | +0.10 pp |
| S1 | **+1.58 pp** | 23.61% | 7.23% | 21.36% | 6.56% | +2.25 pp | +0.67 pp |
| PP | **+1.25 pp** | 15.30% | 5.03% | 13.50% | 4.49% | +1.79 pp | +0.54 pp |
| R1 | **+3.11 pp** | 22.81% | 6.52% | 19.72% | 6.53% | +3.09 pp | -0.01 pp |
| R2 | **+0.69 pp** | 24.07% | 7.05% | 23.64% | 7.31% | +0.43 pp | -0.26 pp |
| R3 | **+0.60 pp** | 24.44% | 9.02% | 23.95% | 9.13% | +0.49 pp | -0.11 pp |

The interaction is the strong-wick core-vs-outer premium minus the weak-wick core-vs-outer premium. It is the appropriate measure because raw terminal rates vary strongly by level and market state.

## 3. Tier comparison — the important result

| Tier | Interaction | Core strong | Core weak | Outer strong | Outer weak |
|---|---:|---:|---:|---:|---:|
| S1+R1 | **+2.39 pp** | 23.20% | 6.86% | 20.48% | 6.55% |
| S2+R2 | **+0.20 pp** | 24.40% | 7.79% | 24.27% | 7.86% |
| S3+R3 | **-0.92 pp** | 23.61% | 9.57% | 24.46% | 9.51% |
| PP | **+1.25 pp** | 15.30% | 5.03% | 13.50% | 4.49% |

**S1/R1 minus S2/R2 = +2.19 pp.** This is the clearest decomposition of the previously pooled Daily/H1 result.

### Pair/year breadth

- 9/10 pair-level S1/R1-minus-S2/R2 contrasts are positive; NZDUSD is the exception in the reference reconstruction.
- 4/4 calendar-year contrasts are positive: 2022 +0.30 pp, 2023 +1.04 pp, 2024 +4.73 pp, 2025 +2.65 pp.
- Pair-year clustered bootstrap: 95% CI [+0.35,+3.96] pp, two-sided sign-mass p≈0.0176.

## 4. What the weak-wick baseline says

The weak-wick terminal rate itself rises as price reaches more remote pivot tiers. In the core it is about **5.03% at PP**, **6.52–7.23% at R1/S1**, **7.05–8.56% at R2/S2**, and **9.02–10.09% at R3/S3**. This is important: outer pivot levels are encountered in different, usually more extended/volatile market states, so comparing raw terminal percentages across R1, R2 and R3 would confound the pivot tier with regime/excursion depth.

What distinguishes S1/R1 is not merely that terminal probability is high there. The decisive feature is that **a strong directional rejection wick becomes more informative when it occurs in the S1/R1 core than it is in the matched outer control zone**, while the same incremental relationship is almost absent at S2/R2.

For pooled S1/R1, the strong-wick pivot proximity premium is about **+2.71 pp**, while the weak-wick proximity premium is only **+0.32 pp**, producing the +2.39 pp interaction. At S2/R2 the strong premium is only about **+0.14 pp** and the weak premium about **−0.07 pp**, leaving essentially no incremental wick interaction.

## 5. Individual interpretation

- **R1 is strongest:** +3.11 pp interaction. Its weak-wick core and outer rates are virtually identical (~6.52% vs ~6.53%), while strong-wick terminal probability is ~22.81% in the core versus ~19.72% outer. This is close to a clean rejection-wick interaction.
- **S1 is also strong:** +1.58 pp. Strong-wick proximity adds ~+2.25 pp, while weak-wick proximity adds ~+0.67 pp.
- **PP remains meaningful:** +1.25 pp. It is not merely an R1/S1 phenomenon, though PP has a distinctly lower raw terminal baseline.
- **S2/R2 are weak as a tier:** −0.29 pp at S2 and +0.69 pp at R2; pooled +0.20 pp.
- **S3/R3 are sparse and unstable:** pooled −0.92 pp. S3 is distinctly negative in this reconstruction; R3 mildly positive. Their cell counts are much smaller and should not drive trading-rule design.

## 6. Reconstruction sensitivity

Because the original heavy terminal ledger is unavailable, five detector-continuity/tie-handling reconstructions were checked. The main tier conclusion does not change:

| Reconstruction | All-level interaction | S1/R1 | S2/R2 | S1/R1 − S2/R2 |
|---|---:|---:|---:|---:|
| no-gap / strict tie | +1.12 pp | +2.39 pp | +0.20 pp | **+2.19 pp** |
| gap-reset / strict tie | +1.12 pp | +2.26 pp | +0.20 pp | **+2.06 pp** |
| no-gap / latest tie | +1.11 pp | +2.37 pp | +0.17 pp | **+2.20 pp** |
| gap-reset / latest tie | +1.10 pp | +2.23 pp | +0.16 pp | **+2.07 pp** |
| full-clock-gap ATR stress | +1.00 pp | +1.77 pp | +0.10 pp | **+1.67 pp** |

Across all five reconstructions the S1/R1 advantage is **+1.67 to +2.20 pp**. Thus the qualitative tier distinction is not an artifact of one candidate-tie or gap-continuity convention.

## 7. Strategic implication

The earlier pooled Daily/H1 result should no longer be interpreted as evidence that all seven daily pivot coordinates contribute equally. The more defensible working model is:

**first-order daily pivot geometry (S1/R1) + observable H1 directional rejection wick = the primary candidate mechanism; PP is a secondary positive context; second- and third-order pivots do not currently justify equal weighting.**

This is mechanistically useful but does **not** authorize dropping S2/R2 from a trading system on this consumed sample. A causal execution study may use this decomposition to define hypotheses, but any level restriction or weighting must be separately preregistered and confirmed on genuinely fresh evidence.

## 8. Scientific disposition

`DIAGNOSTIC_FIRST_ORDER_PIVOTS_DOMINATE_SECOND_ORDER_PIVOTS_REQUIRES_EXACT_LEDGER_OR_FRESH_CONFIRMATION`

No Pine, alerts, sizing, paper trading or live deployment is authorized by this diagnostic.
