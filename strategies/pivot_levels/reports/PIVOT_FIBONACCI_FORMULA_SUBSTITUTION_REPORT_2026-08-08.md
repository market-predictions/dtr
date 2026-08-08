# Fibonacci Pivot Formula Substitution — Internal Report

**Date:** 2026-08-08  
**Study:** `DFXC-20260808-005-pivot-fibonacci-substitution`  
**Work package:** `PIV-WP-20260808-05`  
**Dataset:** Dukascopy FX Cash — ten registered FX pairs  
**Outcome window:** 2015–2021 only  
**New pristine holdout:** none used

## Executive conclusion

Replacing classic floor-pivot coordinates with standard Fibonacci pivot coordinates preserves the Daily→H1 pivot/wick phenomenon clearly and produces a directionally positive Weekly→H4 result. It does **not** establish that Fibonacci pivots are superior to classic pivots.

- **Daily Fibonacci pivots → H1, inherited 0–20% normalized-spacing core:** internally supported. Pivot-specific wick interaction **+1.052 pp**, 95% pair-year clustered-bootstrap CI **[+0.634,+1.473] pp**, Holm p=0.0000, positive in 9/10 pairs, all leave-one-pair-out pooled effects positive. Structural terminal effect **+1.314 pp**, CI **[+1.115,+1.515] pp**.
- **Weekly Fibonacci pivots → H4, inherited SP10 0–10% normalized-spacing core:** positive but statistically marginal. Wick interaction **+1.234 pp**, CI **[+0.012,+2.441] pp**, raw/Holm p=0.0488, positive in 7/10 pairs, all leave-one-pair-out pooled effects positive. Structural effect **+1.159 pp**, CI **[+0.641,+1.667] pp**.
- Paired formula differences do not distinguish Fibonacci from classic pivots: Daily wick delta **+0.122 pp**, CI **[-0.338,+0.573]**; Weekly wick delta **−0.373 pp**, CI **[-1.631,+0.880]**.

Binding implementation decision: `DAILY_FIBONACCI_SUPPORTED_WEEKLY_FIBONACCI_BORDERLINE_FORMULA_NOT_SUPERIOR`.

## 1. Frozen Fibonacci formula

The study changes only the pivot coordinate formula. It uses the standard Fibonacci floor-pivot construction from the prior completed NY17 pivot period:

- `PP = (H+L+C)/3`
- `R1 = PP + 0.382*(H-L)`; `S1 = PP - 0.382*(H-L)`
- `R2 = PP + 0.618*(H-L)`; `S2 = PP - 0.618*(H-L)`
- `R3 = PP + 1.000*(H-L)`; `S3 = PP - 1.000*(H-L)`

No 0.236, 0.786, 1.272, 1.618 or alternative coefficient was inspected.

## 2. Everything else was held fixed

### Daily→H1

- Daily Fibonacci pivots S3…R3.
- H1 midpoint response candles.
- Nearest-pivot local spacing defined by adjacent Fibonacci pivot coordinate.
- Core `0 <= normalized_distance < 0.20`.
- Outer control `0.30 <= normalized_distance <= 0.50`.

### Weekly→H4

- Weekly Fibonacci pivots S3…R3.
- H4 midpoint response candles.
- The successful classic-pivot SP10 geometry was inherited without retuning.
- Core `0 <= normalized_distance < 0.10`.
- Equal-width outer control `0.40 <= normalized_distance <= 0.50`.

### Terminal and wick logic

- ATR24 simple mean, lagged one response candle.
- 0.75×ATR directional-change threshold.
- Candidate terminal endpoints are pivot-blind and wick-blind.
- Strictly-later-bar confirmation: the current candle close first tests the previously stored candidate; only if no reversal is confirmed may the current high/low replace the candidate.
- Strong directional wick `>=30%` of response-candle range; weak `<10%`.
- Frozen wick bins `<10`, `10–20`, `20–30`, `30–40`, `>=40%`.

The primary wick endpoint is `(core strong - core weak) - (outer strong - outer weak)`.

## 3. Daily Fibonacci → H1

| Metric | Result |
|---|---:|
| Development 2015–2019 wick interaction | **+1.292 pp** |
| Validation 2020–2021 wick interaction | **+0.456 pp** |
| Combined wick interaction | **+1.052 pp** |
| 95% CI | **+0.634 to +1.473 pp** |
| Holm p | **0.0000** |
| Positive pair wick interactions | **9/10** |
| Structural terminal effect | **+1.314 pp** |
| Structural 95% CI | **+1.115 to +1.515 pp** |
| Positive pair structural effects | **10/10** |

Every pooled leave-one-pair-out effect is positive for both endpoints.

The Fibonacci Daily core terminal rate also rises monotonically with directional wick severity:

`6.69% → 10.32% → 13.47% → 15.85% → 20.86%`.

So Daily/H1 is not a threshold artifact around exactly 30% wick size.

### Formula comparison

The same reconstructed engine gives classic Daily/H1 wick interaction +0.930 pp. Fibonacci minus classic is therefore +0.122 pp, but the paired cluster-bootstrap interval is **[-0.338,+0.573] pp**. There is no evidence that Fibonacci is better.

Interpretation: **Fibonacci preserves the Daily/H1 phenomenon; formula superiority is unproven.**

## 4. Weekly Fibonacci → H4

| Metric | Result |
|---|---:|
| Development 2015–2019 wick interaction | **+1.480 pp** |
| Validation 2020–2021 wick interaction | **+0.614 pp** |
| Combined wick interaction | **+1.234 pp** |
| 95% CI | **+0.012 to +2.441 pp** |
| Raw / Holm p | **0.0488** |
| Positive pair wick interactions | **7/10** |
| Structural terminal effect | **+1.159 pp** |
| Structural 95% CI | **+0.641 to +1.667 pp** |
| Positive pair structural effects | **9/10** |

Every pooled leave-one-pair-out effect is positive. The five-bin core wick gradient is monotonic:

`6.36% → 9.95% → 12.80% → 16.48% → 21.25%`.

However the wick interval only narrowly clears zero and the adjusted p-value is immediately below 0.05. Weekly/H4 is therefore **borderline**, not equivalent in confidence to Daily/H1.

### Formula comparison

The reconstructed classic SP10 wick interaction is +1.607 pp. Fibonacci minus classic is **−0.373 pp**, with paired 95% CI **[-1.631,+0.880] pp**. That interval includes both meaningful Fibonacci underperformance and some Fibonacci outperformance.

Interpretation: **the data do not distinguish the formulas; Fibonacci is not demonstrated superior and may be modestly weaker on Weekly/H4.**

## 5. Classic comparator reproduction and residual limitation

The preregistration required a same-engine classic comparator because the terminal labels are formula-independent and a formula substitution is only interpretable if the parent phenomenon is reconstructed.

During implementation, an initially incorrect update-before-confirmation endpoint ordering produced a material wick-distribution drift. That run was rejected before Fibonacci conclusions were accepted. The frozen anti-circularity amendment was then recovered and applied exactly: the current response candle first tests the candidate established on a strictly earlier candle; only a non-confirming candle may replace that candidate.

After that correction, the primary classic wick endpoints reproduce extremely closely:

| Horizon | Frozen parent | Reconstructed | Absolute error |
|---|---:|---:|---:|
| Daily/H1 classic wick | +0.921 pp | +0.930 pp | **0.009 pp** |
| Weekly/H4 SP10 classic wick | +1.616 pp | +1.607 pp | **0.009 pp** |

The reconstructed structural effects retain a larger residual:

- Daily/H1: +1.127 pp versus frozen +1.023 pp, absolute difference **0.103 pp**;
- Weekly/H4: +1.068 pp versus frozen +1.002 pp, difference **0.066 pp**.

The original large parent runner/terminal ledger was intentionally not committed, so that residual cannot be eliminated by exact ledger replay in the current environment. It is recorded rather than hidden.

This residual does not threaten the Daily Fibonacci conclusion because its wick CI is far above zero. It **does matter for Weekly**, whose lower confidence bound is only +0.012 pp. Consequently Weekly Fibonacci is recorded as a borderline internal result pending independent reconstruction/fresh confirmation rather than promoted as a mature finding.

## 6. Pair breadth

Daily Fibonacci wick interaction is positive in 9/10 pairs; EURJPY is negative. Daily structural effect is positive in all ten.

Weekly Fibonacci wick interaction is positive in 7/10 pairs. AUDUSD, GBPJPY and USDCHF are negative; GBPJPY is the largest negative. Weekly structural effect is positive in 9/10, with AUDUSD slightly negative.

No pair is removed and no named pivot is selected.

## 7. What this says about pivot mathematics

The useful conclusion is not “Fibonacci pivots beat classic pivots.” They do not, based on this evidence.

A more defensible interpretation is that the observed exhaustion relationship is **not uniquely dependent on the classic floor-pivot algebra**. Daily/H1 survives when the seven pivot coordinates are redistributed symmetrically around the same PP by Fibonacci fractions of the prior range. Weekly/H4 remains directionally present but weaker/more uncertain.

This suggests the mechanism may involve **range-derived reference geometry and local proximity**, rather than market participants responding uniquely to one exact pivot formula. That is strategically important because it cautions against treating any one pivot calculation as mystical or privileged.

## 8. Scientific status and next step

### Daily/H1 Fibonacci

Status: **SUPPORTED_INTERNAL**.

It is not eligible to reuse 2022–2025 as a pristine Fibonacci holdout because those years have already been exposed in the related Daily/H1 classic-pivot programme. A clean Fibonacci confirmation needs genuinely fresh evidence or another qualified independent dataset.

### Weekly/H4 Fibonacci

Status: **BORDERLINE / INDETERMINATE FOR PROMOTION**.

The point estimate passes the frozen numerical gate in the reconstructed engine, but the lower CI and p-value are marginal enough that the comparator reproduction residual is scientifically material. Do not promote it as equivalent to the already stronger classic SP10 candidate.

## 9. Prohibited rescue

Do not use this sample to:

- test different Fibonacci ratios;
- alter the Daily 20% or Weekly 10% zone;
- add ATR caps;
- drop AUDUSD/GBPJPY/USDCHF or any other pair;
- select PP/R1/S1 or another named pivot;
- change wick thresholds;
- add session filters;
- use 2022–2025 to choose the preferred formula.

Any such extension is a new hypothesis.

## Bottom line

**Daily Fibonacci pivots work as an alternative representation of the already observed Daily/H1 pivot-zone exhaustion phenomenon, but they do not outperform classic pivots. Weekly Fibonacci/H4 is promising but much less secure; the classic Weekly SP10 formulation remains the stronger current candidate.**
