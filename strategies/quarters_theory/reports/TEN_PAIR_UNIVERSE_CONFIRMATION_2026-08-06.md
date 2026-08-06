# Quarters Theory Ten-Pair Stage-1 Universe Confirmation

**Decision:** `CONFIRM_GLOBAL_DEMOTION_NO_PAIR_EXCEPTIONS`

The canonical 250-pip Large Quarter Point hypothesis is demoted across the registered ten-pair Dukascopy FX universe. None of the seven new confirmation pairs met the preregistered positive-and-stable criterion, and none of the ten pairs did so overall.

## Frozen test

- Candidate levels every 50 pips; canonical phase 0 modulo 250 pips.
- Controls at phases 50, 100, 150 and 200.
- Mid-close crossing and 25-pip directional rearm.
- Primary endpoint: direction-aligned midpoint return after 60 minutes.
- Matching: year, direction, whole/half-100 roundness and four-hour UTC session.
- Uncertainty: 5,000-draw year-preserving weekly block bootstrap.
- Development: 2015–2019; internal validation: 2020–2021.
- 2022–2025 remained unopened; no strategy optimization was performed.

## Pair results

| Pair | Events | LQP | Development | Validation | Combined | Combined 95% CI | Stable |
|---|---:|---:|---:|---:|---:|---:|:---:|
| AUDUSD | 2779 | 551 | 0.203 | 2.560 | 1.020 | [-0.495, 2.606] | no |
| EURGBP | 2461 | 470 | -3.112 | 1.347 | -1.932 | [-5.775, 1.606] | no |
| EURJPY | 5652 | 1099 | -0.267 | -0.788 | -0.369 | [-2.040, 1.458] | no |
| EURUSD | 3743 | 709 | 0.532 | -0.805 | 0.246 | [-1.599, 2.029] | no |
| GBPJPY | 11614 | 2379 | -0.240 | -1.162 | -0.423 | [-2.335, 1.234] | no |
| GBPUSD | 6843 | 1373 | -0.789 | -0.754 | -0.780 | [-2.575, 1.195] | no |
| NZDUSD | 2722 | 564 | 0.200 | -0.871 | -0.109 | [-1.641, 1.751] | no |
| USDCAD | 4750 | 946 | -0.330 | -2.472 | -0.918 | [-2.559, 0.717] | no |
| USDCHF | 3037 | 635 | -2.997 | -0.645 | -2.578 | [-7.290, 0.368] | no |
| USDJPY | 3677 | 754 | 0.784 | -3.239 | -0.036 | [-2.111, 1.912] | no |

## Universe diagnostics

- Total eligible crossings: **47,278**.
- Canonical LQP crossings: **9,480**.
- Positive/stable pairs: **0 / 10**.
- Positive development estimates: **4 / 10** (AUDUSD, EURUSD, NZDUSD, USDJPY).
- Positive validation estimates: **2 / 10** (AUDUSD, EURGBP).
- Positive combined point estimates: **2 / 10** (AUDUSD, EURUSD).
- Development-to-validation sign flips: **4 / 10** (EURGBP, EURUSD, NZDUSD, USDJPY).
- Median combined effect: **-0.396 pips**.

## Interpretation

The evidence does not support a privileged continuation effect at canonical 250-pip levels relative to nearby round-number controls. AUDUSD was positive in both periods, but its combined interval crossed zero and therefore did not qualify. Several pairs reversed sign between development and validation, which argues against temporal stability rather than for a hidden universal effect.

This result closes the basic-principle validation line. It does not prove that all quarter-level trading ideas are impossible; it shows that the specific first-principles claim tested here—canonical 250-pip levels possess a distinct short-horizon continuation edge—did not survive matched controls and cross-pair validation.

Not authorized: threshold rescue, pair shopping, transition census, strategy entries, stops, targets, P&L optimization, Pine implementation, alerts, sizing or deployment.

## Source and integrity

The study used the registered **Dukascopy FX Cache**. Annual BID/ASK source hashes were verified before analysis. GBPUSD, EURUSD and USDJPY reproduced their frozen reference results; JPY pairs used the exact adapter write-and-reload normalization path to avoid floating-point boundary drift.
