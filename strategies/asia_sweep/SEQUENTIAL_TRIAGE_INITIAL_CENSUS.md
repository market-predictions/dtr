# Sequential Triage — Initial Development Census

Date: 2026-07-26
Status: `PRELIMINARY_DIAGNOSTIC_NOT_GATE_DECISION`
Source: retained 2015–2019 EURUSD/GBPUSD causal landmark ledger from PR #54

## State prevalence

| Landmark | Reversal | Continuation | Abstain | Rows |
|---|---:|---:|---:|---:|
| T0 | 23.86% | 32.20% | 43.93% | 2,506 |
| T1 | 24.95% | 31.26% | 43.79% | 2,393 |
| T2 | 26.44% | 29.95% | 43.61% | 2,254 |
| T3 | 27.38% | 29.05% | 43.57% | 2,162 |

The three classes are sufficiently populated for multiclass modelling. Abstention remains structurally stable while already-resolved continuation events leave the surviving population.

## Preliminary leave-one-year-out diagnostic

These figures use the frozen causal feature set and fixed diagnostic models. They are not the authoritative nested threshold/gate result.

### Top-quintile precision and lift

| Landmark/model | Continuation precision | Continuation lift | Reversal precision | Reversal lift |
|---|---:|---:|---:|---:|
| T0 logistic | 51.79% | 1.61x | 31.87% | 1.34x |
| T0 HGB | 50.20% | 1.56x | 33.86% | 1.42x |
| T1 logistic | 59.58% | 1.91x | 37.50% | 1.50x |
| T1 HGB | 57.71% | 1.85x | 36.25% | 1.45x |
| T2 logistic | 61.73% | 2.06x | 43.81% | 1.66x |
| T2 HGB | 63.27% | 2.11x | 39.82% | 1.51x |
| T3 logistic | 61.75% | 2.13x | 47.00% | 1.72x |
| T3 HGB | 62.90% | 2.17x | 45.39% | 1.66x |

Every reversal and continuation diagnostic showed positive top-quintile lift in both pairs and all five development years.

## Interpretation

- Continuation becomes identifiable earlier and more strongly than reversal.
- T1 already has useful continuation discrimination, which may support an early cancel/exit action.
- Reversal reaches the preregistered 40% precision region around T2/T3, but the authoritative decision requires fold-local thresholds, calibration and abstention coverage.
- This supports continuing Phase A. It does not authorize staged-entry P&L.

## Next gate work

1. implement fold-local multinomial calibration and threshold selection;
2. calculate actionable reversal/continuation coverage and explicit abstention rate;
3. verify balanced utility, pair/year breadth and concentration;
4. open Phase B only if every frozen triage gate passes.
