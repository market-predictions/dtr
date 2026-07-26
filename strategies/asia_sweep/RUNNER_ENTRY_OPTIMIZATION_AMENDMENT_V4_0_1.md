# Runner and Entry Optimisation Amendment v4.0.1

Date: 2026-07-26  
Binding on: `RUNNER_ENTRY_OPTIMIZATION_CONTRACT_V4_0.md`

## TP1 timing clarification

The Asian midpoint is TP1 but is not subject to the previous 10:00 deadline.

For each candidate runner policy:

- the full position remains active from the fixed market entry until the first of the original stop, TP1 or the policy time exit;
- if TP1 is first reached at any active minute before the policy time exit, 50% exits at TP1 and the remaining 50% becomes the runner;
- if TP1 is never reached, the full position exits at the policy time exit;
- a runner can therefore begin after 10:00, provided it begins before the frozen 12:00/14:00/16:00/18:00 policy deadline.

This replaces the prior staged-exit rule that required TP1 before 10:00.

## Deployable modal-policy safeguards

In addition to the out-of-fold selection gates, the modal policy intended for the next partition must satisfy on the complete 2015–2019 discovery sample:

- positive base expectancy;
- positive 0.10-pip-stressed expectancy;
- positive expectancy on both EURUSD and GBPUSD;
- positive expectancy in at least four of five years.

These checks do not select the modal policy; they only prevent authorization when the cross-fold modal choice itself is not broadly viable.

## Outcome-access statement

This amendment was frozen before the 40-policy runner ledger or any runner policy metric was generated.
