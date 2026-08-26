# Stage-1 Distinctiveness Report — GBP/USD

**Date:** 2026-08-05  
**Result:** Gate 0 not passed  
**Data:** Dukascopy M1 bid/ask, 2015-2021  
**Reserved holdout:** 2022-2025 outcome-unopened

## Executive conclusion

The canonical 250-pip Quarters grid did not show a positive short-horizon continuation advantage over other 50-pip round levels after matching ordinary 100-pip roundness.

The primary 60-minute estimate was **-0.78 pip**, with a year-preserving weekly-block 95% interval of **-2.58 to +1.20 pips**. Development and internal-validation point estimates were both negative. The adjusted probability of reaching +10 pips before -10 pips was effectively identical at canonical and control levels.

This is not evidence for a tradable continuation edge. It is evidence against proceeding directly to strategy optimization.

## Data audit

| Measure | Result |
|---|---:|
| Calendar-minute rows | 3,682,080 |
| Active bid-and-ask minutes | 2,612,846 |
| Duplicate timestamps | 0 |
| Non-positive timestamp deltas | 0 |
| Negative active spreads | 0 |
| Annual checksum failures | 0 |
| Median annual spread | 0.8-1.1 pips |
| Annual 95th-percentile spread | 1.7-2.8 pips |

The private development archive SHA-256 was `5be9c8c26b1a1d35e271aa004e932e3ee77698cc29404f59be973f5678826013`.

## Event census

| Period | All events | Canonical LQP | Matched non-LQP round levels |
|---|---:|---:|---:|
| 2015-2021 | 6,843 | 1,373 | 5,470 |

The detector rearms separately for each level and direction after price returns 25 pips to the origin side. Calendar-week block inference handles remaining event clustering.

## Primary effect

The estimator compares phase 0 modulo 250 pips against phases 50, 100, 150 and 200 within year, direction, whole/half-100 class and four-hour UTC session strata.

| Period | Canonical effect | 95% block interval |
|---|---:|---:|
| Development 2015-2019 | -0.79 pip | -3.00 to +1.80 pips |
| Internal validation 2020-2021 | -0.75 pip | -3.20 to +1.67 pips |
| All 2015-2021 | **-0.78 pip** | **-2.58 to +1.20 pips** |

The sign was consistently adverse, although uncertainty includes zero.

## Horizon profile

Across the full period, the canonical phase ranked last among five phases at 5, 60, 120 and 240 minutes. It did not produce a stable positive rank in internal validation. The one-day result was unstable and changed sign between development and validation, which is inconsistent with a robust fixed-grid mechanism.

## First-passage result

Excluding timeout and same-minute ambiguity, a covariate-adjusted binomial model with week-clustered uncertainty estimated:

- canonical odds ratio for +10 before -10 pips: **1.02**;
- 95% interval: **0.89-1.17**;
- p-value: **0.79**.

Raw follow-through rates were 48.4% at LQPs and 48.3% at controls. There was no immediate acceleration advantage.

## Covariate-adjusted return result

The 60-minute LQP coefficient after controlling for year, direction, roundness, session, month, 500-pip price band, prior 60-minute movement, prior four-hour range, crossing overshoot and spread was:

| Period | Adjusted coefficient | 95% interval |
|---|---:|---:|
| Development | -0.11 pip | -1.95 to +1.74 |
| Internal validation | -0.95 pip | -3.14 to +1.24 |
| All | -0.21 pip | -1.68 to +1.27 |

The exact negative magnitude is model-dependent; the absence of a positive advantage is not.

## Reset sensitivity

| Reset | Events | All-period 60m effect | 95% interval |
|---:|---:|---:|---:|
| 15 pips | 10,500 | -0.66 pip | -1.91 to +0.66 |
| 25 pips | 6,843 | -0.78 pip | -2.58 to +1.20 |
| 50 pips | 3,678 | -1.73 pips | -4.57 to +1.51 |

A stricter or looser rearm definition did not reveal a positive canonical effect.

## Crossing-quality sensitivity

Caps on crossing overshoot and spread did not produce a replicating positive result. A development-only +0.36-pip estimate under a 10-pip overshoot cap became -1.22 pips in internal validation. This is exactly the type of non-replicating sensitivity that must not become a filter.

## Harsh interpretation

The study does not prove that price ignores round numbers. It shows that the canonical 250-pip subset was not better than other comparable round levels in the first test that should have favoured a genuine microstructural effect.

The upper 95% bound of +1.20 pips is small relative to the observed median spread near one pip. Even if the true effect were near that upper bound, converting it into an executable strategy would leave little margin for entry timing, adverse selection, slippage and financing.

## Decision

- Do not optimize C1, C2, C3 or R1 on GBP/USD.
- Do not open 2022-2025.
- Replicate the same Stage-1 engine on EUR/USD and one JPY pair if data are readily available.
- Continue to the 25/75/125/225 episode programme only if cross-pair replication shows positive, stable incremental LQP information.

The current programme is therefore **demoted, not universally terminated**.
