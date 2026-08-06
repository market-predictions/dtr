# Quarters Theory Destination and Exhaustion Study

Date: 2026-08-07  
Programme: `QT-DESTINATION-EXHAUSTION-V1`  
Work package: `QT-WP-20260807-04`

**Binding decision:** `REJECT_DESTINATION_EXHAUSTION_MECHANISM`

## Executive conclusion

The alternative Quarter Theory mechanism is not supported by the registered ten-pair Dukascopy FX evidence over 2015–2021. Canonical 250-pip levels did not attract independent trend endpoints, did not improve completion of a causally qualified approach, and did not produce a stable excess of reversal over equal-sized extension after arrival.

This is a different and stronger negative result than the earlier continuation study. The new programme explicitly treated the 250 level as a possible destination and exhaustion zone, but all three preregistered primary effects were approximately zero, temporally unstable, statistically weak after Holm correction, and insufficiently broad across pairs.

## Frozen design

- Ten FX pairs from the permanent Dukascopy FX Cache; M1 separate BID/ASK, UTC.
- Midpoint structural analysis in native source pips; no JPY quote normalization ambiguity.
- Development: 2015–2019.
- Internal validation: 2020–2021.
- 2022–2025 remained unopened.
- A1: H1 ATR directional-change leg terminal clustering within ±15 pips of phase 0 versus phases 50/100/150/200.
- A2: causal four-hour trend approaches, target-before-0.50-ATR-failure over 24 hours, matched by pair/year/direction/session/distance/ATR/efficiency.
- A3: after successful arrival, 25-pip reversal before 25-pip extension over four hours, using the same matched context.
- 5,000 pair-week bootstrap draws and Holm correction across A1/A2/A3.

## Primary results

| Test | Development | Validation | Combined | 95% interval | Raw p | Holm p | Positive pairs | Pass |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| A1 | -0.000529 | +0.001780 | +0.000136 | [-0.004515, +0.004970] | 0.9428 | 1.0000 | 6/10 | no |
| A2 | +0.012759 | -0.030446 | +0.000422 | [-0.028827, +0.024433] | 0.8784 | 1.0000 | 5/10 | no |
| A3 | +0.026922 | -0.031310 | +0.009464 | [-0.085587, +0.091110] | 0.9152 | 1.0000 | 6/10 | no |

All three mechanisms changed sign or failed direction between development and validation. Every combined interval spans zero. Holm-adjusted p-values are 1.0.

## A1 — Trend-leg terminal clustering

- Confirmed independent H1 directional-change endpoints: **272,065**.
- Primary pooled score: canonical proximity minus average control-phase proximity.
- Development: **-0.000529**.
- Validation: **+0.001780**.
- Combined: **+0.000136**, 95% interval **[-0.004515, +0.004970]**.

| Phase | Endpoints within ±15 pips | Share of all endpoints |
|---:|---:|---:|
| 0 | 32,706 | 12.02% |
| 50 | 32,574 | 11.97% |
| 100 | 33,037 | 12.14% |
| 150 | 33,440 | 12.29% |
| 200 | 31,625 | 11.62% |

Canonical phase 0 captured 12.02% of endpoints, almost exactly the same as the control phases. Phase 150, not phase 0, had the highest descriptive share. The canonical effect was negative in development and positive in validation, so the required temporal direction failed.

## A2 — Destination completion

- Qualified causal approach episodes: **47,571**.
- Matched observations contributing to the combined estimator: **7,190** canonical and **13,621** control across **5,411** matched strata.
- Development matched effect: **+0.012759**.
- Validation matched effect: **-0.030446**.
- Combined matched effect: **+0.000422**, 95% interval **[-0.028827, +0.024433]**.

| Target class | Episodes | Target first | Failure first | Timeout | Raw signed mean |
|---|---:|---:|---:|---:|---:|
| Canonical 250 | 9,430 | 2,171 (23.02%) | 6,964 (73.85%) | 291 (3.09%) | -0.508271 |
| Control phases | 38,141 | 8,730 (22.89%) | 28,217 (73.98%) | 1,178 (3.09%) | -0.510920 |

The raw target-first rate was 23.02% for canonical destinations and 22.89% for controls. After frozen matching, the difference was effectively zero. The development estimate was positive, but validation reversed materially negative. Only 5 of 10 pair-level effects were positive and the leave-one-pair-out effect changed sign.

## A3 — Reversal after arrival

- Successful A2 arrivals entering the reaction test: **10,901**.
- Matched observations contributing to the combined estimator: **805** canonical and **1,075** control across **741** matched strata.
- Development matched effect: **+0.026922**.
- Validation matched effect: **-0.031310**.
- Combined matched effect: **+0.009464**, 95% interval **[-0.085587, +0.091110]**.

| Arrival class | Arrivals | Reversal first | Extension first | Timeout | Raw signed mean |
|---|---:|---:|---:|---:|---:|
| Canonical 250 | 2,171 | 624 (28.74%) | 656 (30.22%) | 888 (40.90%) | -0.014740 |
| Control phases | 8,730 | 2,437 (27.92%) | 2,661 (30.48%) | 3,614 (41.40%) | -0.025659 |

Canonical arrivals showed a small descriptive reduction in extension bias, but the matched effect was tiny, highly uncertain, and reversed from positive development to negative validation. The evidence does not support a distinctive reversal zone.

## Pair breadth

| Pair | A1 clustering | A2 destination | A3 reversal |
|---|---:|---:|---:|
| AUDUSD | +0.002566 | -0.022968 | -0.091284 |
| EURGBP | +0.007980 | -0.047686 | +0.026140 |
| EURJPY | +0.005991 | -0.024380 | +0.106965 |
| EURUSD | -0.016154 | +0.021782 | -0.075481 |
| GBPJPY | +0.002974 | +0.030796 | +0.041440 |
| GBPUSD | -0.006966 | -0.001283 | +0.033786 |
| NZDUSD | +0.002555 | -0.041589 | +0.039049 |
| USDCAD | -0.002270 | +0.033620 | -0.011337 |
| USDCHF | +0.006209 | +0.059903 | +0.075726 |
| USDJPY | -0.002054 | +0.009052 | -0.088766 |

Pair signs were mixed and no primary test met the preregistered six-pair breadth plus positive leave-one-pair-out requirement.

## Independent assurance

- Assurance verdict: **`PASS`**.
- Reverified all 70 annual compressed BID/ASK source partitions against embedded and recorded SHA-256 values.
- Recomputed A1 scores and all A1/A2/A3 development, validation and combined point estimates independently.
- Confirmed exact pair membership, event counts, phase domain and absence of 2022–2025.
- Ran a separate 2,000-draw pair-week bootstrap with a different seed; all three independent 95% intervals again spanned zero.

| Test | Independent 95% interval | Independent p |
|---|---:|---:|
| A1 | [-0.004406, +0.004961] | 0.9870 |
| A2 | [-0.030383, +0.025445] | 0.8360 |
| A3 | [-0.082251, +0.087653] | 0.9520 |

## Decision and roadmap consequence

Binding decision: **`REJECT_DESTINATION_EXHAUSTION_MECHANISM`**.

The original intuition was worth testing because it represented a genuinely different mechanism. The data do not support that mechanism under the preregistered definitions. Canonical 250-pip levels were neither privileged terminal destinations nor stable reversal zones relative to the other phases of the same 50-pip lattice.

Not authorized:

- threshold or ATR sensitivity searches;
- changing the endpoint window after seeing the phase counts;
- selecting individual pairs with favorable descriptive signs;
- opening 2022–2025 to rescue the result;
- designing entries, targets, stops, P&L, Pine, alerts or sizing from this mechanism.

A future Quarter-related study would need genuinely new information not present in this price-only M1/H1 design—for example independently sourced order-flow, options barriers, dealer positioning or event-specific liquidity evidence—and should compete with other research priorities rather than continue parameter subdivision.
