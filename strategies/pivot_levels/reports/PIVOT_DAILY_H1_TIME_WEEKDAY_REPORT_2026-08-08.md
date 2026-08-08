# Daily S1/R1 × H1 Rejection — Time-of-Day and Weekday Study

**Date:** 2026-08-08  
**Study:** `DFXC-20260808-007-pivot-daily-time-weekday`  
**Dataset:** Dukascopy FX Cash — ten registered FX pairs  
**Window:** 2015–2025; 2026 untouched  
**Study type:** causal/forward heterogeneity on exposed historical data

## Executive conclusion

The proposed **time + price** hypothesis was tested with Tokyo, London and New York FX session Hours 1, 2 and 3 kept separate, plus weekday Monday–Friday. The result is mostly negative for **directional reversal edge** and positive for **movement magnitude**.

- No one of the **nine preregistered session-hour comparisons** produces a statistically defensible improvement in the primary 4H ATR-normalized reversal return after Holm correction.
- Global FWD4 session-phase heterogeneity is not supported: cluster-robust omnibus p ≈ **0.33**.
- Weekday heterogeneity is not supported: omnibus p ≈ **0.55**.
- The initially interesting 2022–2025 **third-hour** pattern does **not** replicate over 2015–2021. Pooled H3 versus H1/H2 across 2015–2025 is only **+0.007 ATR**, 95% CI approximately **[-0.033,+0.045]**, p≈0.72.
- The underlying S1/R1 + strong H1 rejection signal itself has mean FWD4 reversal return **−0.009 ATR**, 95% clustered-bootstrap CI approximately **[-0.023,+0.005]**. The confirmed retrospective terminal association therefore does not automatically become an immediate reversal trade.
- Time does matter strongly for **volatility/path shape**: London H1→H3 and New York H1→H2 materially increase both favorable and adverse 4H excursion, while Tokyo H2→H3 suppresses both. This is largely generic session behavior rather than an S1/R1-specific directional premium.

Binding implementation decision:

`NO_MATERIAL_DIRECTIONAL_TIME_OR_WEEKDAY_EDGE_TIME_MAINLY_MODULATES_MOVEMENT_MAGNITUDE`

## 1. Frozen session design

Session clocks were DST-safe local-market definitions:

- Tokyo: 09:00, 10:00, 11:00 JST = H1/H2/H3.
- London: 08:00, 09:00, 10:00 Europe/London.
- New York FX: 08:00, 09:00, 10:00 America/New_York.
- all other H1 bars = `NON_TRANSITION`.

The signal is observed at the H1 close. Forward measurement begins at the next **contiguous** H1 open; weekend/holiday gaps are not bridged. Primary endpoint is direction-adjusted four-hour close return divided by lagged H1 ATR24.

## 2. Causal baseline

| Signal/control | Mean FWD4 | 95% CI / comparison | N |
|---|---:|---:|---:|
| S1/R1 core + strong wick | **−0.009 ATR** | [-0.023,+0.005] | 64,771 |
| S2/R2 core + strong wick | −0.018 ATR | — | 17,351 |
| S1/R1 outer + strong wick | −0.015 ATR | — | 89,996 |
| S1/R1 − S2/R2 | +0.009 ATR | [-0.021,+0.039] | — |
| S1/R1 − outer | +0.006 ATR | [-0.013,+0.026] | — |

The forward baseline is therefore not a positive reversal strategy. S1/R1 is modestly less negative than the controls, but the differences are not statistically secure.

## 3. Primary session-hour results

All values below are S1/R1 mean FWD4 and phase-minus-non-transition effect. Non-transition mean is **−0.0045 ATR**.

| Phase | Mean FWD4 | Phase premium | 95% CI | Holm p |
|---|---:|---:|---:|---:|
| Tokyo H1 | −0.012 | −0.007 | [-0.078,+0.063] | 1.000 |
| Tokyo H2 | +0.026 | +0.031 | [-0.027,+0.091] | 1.000 |
| Tokyo H3 | +0.035 | +0.040 | [-0.016,+0.097] | 1.000 |
| London H1 | −0.043 | −0.038 | [-0.096,+0.020] | 1.000 |
| London H2 | −0.044 | −0.039 | [-0.098,+0.020] | 1.000 |
| London H3 | +0.002 | +0.007 | [-0.056,+0.070] | 1.000 |
| New York H1 | +0.022 | +0.026 | [-0.031,+0.085] | 1.000 |
| New York H2 | −0.041 | −0.036 | [-0.090,+0.020] | 1.000 |
| New York H3 | −0.049 | −0.045 | [-0.093,+0.005] | 0.666 |

No primary session phase passes. The omnibus test across phase categories also fails.

## 4. What happened to the third-hour hypothesis?

In 2022–2025 alone, pooled H3 looked substantially better: mean **+0.042 ATR**, while pooled H1 and H2 were negative. That pattern motivated special scrutiny but was not selected after the fact.

Historical stability rejects the simple third-hour claim:

| Partition | H1 vs non-transition | H2 vs non-transition | H3 vs non-transition |
|---|---:|---:|---:|
| 2015–2019 | +0.042 | −0.015 | **−0.028** |
| 2020–2021 | −0.033 | +0.000 | **−0.039** |
| 2022–2025 | −0.050 | −0.046 | **+0.037** |

Thus H3 is a **recent-sample phenomenon**, not a durable session law. A 4H cooldown robustness check reaches the same conclusion: phase omnibus p≈0.32 and pooled H3 only +0.011 ATR versus non-transition.

### One non-promoted clue: Tokyo H3

Tokyo H3 has a positive FWD4 phase premium in all three partitions (+0.006, +0.113, +0.047 ATR), but the combined confidence interval crosses zero and the effect is not first-order-pivot specific. The S1/R1 outer control also improves around Tokyo H3. It is retained only as a fresh-data observation, not a rule.

## 5. Very-short-horizon behavior

Session phase has a detectable **global** relationship with FWD1 and FWD2 (cluster-robust omnibus p≈0.021 and p≈0.007 respectively), but no individual session hour survives the nine-comparison Holm family. Examples with raw, non-promotional evidence include:

- New York H1: +0.035 ATR at 1H and +0.053 ATR at 2H versus non-transition;
- New York H3: −0.027 ATR at 1H and −0.042 ATR at 2H;
- Tokyo H3: +0.027 ATR at 1H and +0.043 ATR at 2H;
- London H1: −0.024 ATR at 1H and −0.045 ATR at 2H.

These differences either weaken across historical partitions or appear similarly in controls. They do not justify a selected session filter.

## 6. Time strongly changes movement magnitude

This is the clearest positive time finding. Relative to non-transition S1/R1 signals:

| Phase | Δ MFE4 | Δ MAE4 | Interpretation |
|---|---:|---:|---|
| Tokyo H2 | **−0.185 ATR** | **−0.216 ATR** | quieter path |
| Tokyo H3 | **−0.162 ATR** | **−0.208 ATR** | quieter path |
| London H1 | **+0.115 ATR** | **+0.154 ATR** | expansion begins |
| London H2 | **+0.247 ATR** | **+0.267 ATR** | stronger expansion |
| London H3 | **+0.406 ATR** | **+0.365 ATR** | strongest London expansion |
| New York H1 | **+0.403 ATR** | **+0.327 ATR** | strong expansion |
| New York H2 | **+0.236 ATR** | **+0.252 ATR** | continued expansion |

The MFE and MAE confidence intervals for these effects are well away from zero. But both favorable and adverse excursion expand together. The effect also appears in S1/R1 outer and S2/R2 controls. Therefore this is best interpreted as **session-conditioned volatility / path amplitude**, not directional pivot timing edge.

This may later matter for stop distance, target distance, expected holding time and whether a fixed-R execution model is appropriate.

## 7. Weekday

Combined S1/R1 FWD4 means:

- Monday: −0.017 ATR
- Tuesday: +0.000 ATR
- Wednesday: −0.027 ATR
- Thursday: +0.007 ATR
- Friday: −0.010 ATR

Weekday omnibus p≈**0.55**. The recent 2022–2025 Tuesday-vs-Wednesday contrast is not durable: 2020–2021 actually reverses that relationship. No weekday filter is supported.

Because neither the primary session-phase family nor weekday heterogeneity passes, **session × weekday combinations are deliberately not mined** in this study.

## 8. Data/reproduction validation

- ten canonical Dukascopy FX Cash pairs;
- 180,010 strong-wick signal/control observations;
- 68,118 S1/R1 core observations;
- 64,771 valid contiguous FWD4 outcomes;
- 18,583 S2/R2 core controls;
- 93,309 S1/R1 outer controls;
- the independently rebuilt full-history engine reproduces the earlier 2022–2025 event keys, groups, distances, wick values, ATR values and all forward/excursion fields **exactly** for all 65,135 recent-sample events.

A 4H same-side/group cooldown reduces overlapping events materially but leaves the scientific conclusion unchanged.

## 9. Strategic interpretation

The price-time hypothesis should **not** currently be expressed as “S1/R1 reversal works at session Hour X.” The data support a different statement:

> **Session time strongly changes the amount and speed of post-signal movement, but not in a stable way that tells us the reversal direction.**

That distinction matters. Time may be valuable later in the **execution layer**—stop/target geometry, holding horizon, expected volatility and perhaps confirmation requirements—without being a directional entry filter.

The current evidence also warns against assuming that a retrospective terminal association implies immediate mean reversion after the wick close. It does not.

## 10. Next scientific gate

Do not optimize more hours or weekdays on 2015–2025. The next useful work is to design an execution model that treats:

1. S1/R1 proximity + rejection as structural context;
2. session phase as a volatility/path variable rather than a direction selector;
3. explicit event rearm/cooldown;
4. executable BID/ASK entries;
5. pre-frozen stop/target families that can exploit different session volatility without mining time windows.

Any future claim that Tokyo H3 or another specific time is directionally superior must be tested on genuinely fresh post-cache data or an independent qualified dataset.

## Binding disposition

`NO_MATERIAL_DIRECTIONAL_TIME_OR_WEEKDAY_EDGE_TIME_MAINLY_MODULATES_MOVEMENT_MAGNITUDE`

Live trading / Pine / alerts / sizing: **NOT AUTHORIZED**.
