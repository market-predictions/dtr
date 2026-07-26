# Asian Sweep Sequential Triage — Phase A Decision

Date: 2026-07-26
Decision: `PASS_TRIAGE_AUTHORIZE_SEPARATE_STAGED_REVERSAL_AND_CONTINUATION_GEOMETRY`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30203426056`;
- evaluated head: `4615839aade50bfd52fa60ce8ab7e336336d94c9`;
- decision artifact: `asia-sweep-sequential-triage-phase-a-decision`;
- artifact digest: `sha256:6bf572e6751b252b4a27d927fcc96cf996540d05a9dc4f3366bf6cab57fdd32f`.

All eight frozen candidates completed, the aggregate decision artifact uploaded, and the final scientific enforcement passed.

## Selected sequence

The deterministic family hierarchy selected the interpretable multinomial elastic-net sequence.

Both directional roles are assigned at T2:

- continuation-protection landmark: `T2`;
- reversal-confirmation landmark: `T2`.

HGB also passed at T2, but did not satisfy the preregistered replacement requirement over the passing elastic-net sequence.

## T2 selected results

Population: 2,254 unresolved events.

| Metric | Result |
|---|---:|
| Abstention | 69.30% |
| Actionable coverage | 30.70% |
| Continuation decisions | 374 |
| Continuation coverage | 16.59% |
| Continuation precision | 64.44% |
| Reversal decisions | 318 |
| Reversal coverage | 14.11% |
| Reversal precision | 42.45% |
| Macro one-vs-rest PR-AUC relative lift | 73.21% |
| Maximum action concentration | 56.21% |

Class-level discrimination and calibration:

| State | Base rate | PR-AUC | Relative lift | Brier | Constant Brier |
|---|---:|---:|---:|---:|---:|
| Abstain | 43.61% | 0.6752 | +54.82% | 0.2083 | 0.2459 |
| Continuation | 29.95% | 0.6125 | +104.55% | 0.1571 | 0.2098 |
| Reversal | 26.44% | 0.4238 | +60.26% | 0.1794 | 0.1945 |

## Breadth

Continuation precision:

- EURUSD: 64.46%;
- GBPUSD: 64.42%;
- positive decisions in all five years;
- year precision range: 55.84% to 74.19%;
- positive decisions on every weekday and both sweep directions.

Reversal precision:

- EURUSD: 41.61%;
- GBPUSD: 43.09%;
- positive decisions in all five years;
- year precision range: 36.96% to 48.08%;
- positive decisions on every weekday and both sweep directions.

## Threshold audit

Thresholds were selected entirely inside each four-year training partition. The outer-year thresholds were reproduced exactly:

- reversal threshold: 0.30 in four folds and 0.40 in one fold;
- continuation threshold: 0.55 in four folds and 0.60 in one fold;
- conflict margin: 0.00 in four folds and 0.10 in one fold.

Reapplying these thresholds to the retained calibrated probabilities reproduced all 2,254 decisions with zero discrepancy.

## Interpretation

The split decision tree is viable at T2:

- sufficiently strong reversal evidence can authorize a staged reversal hold/add decision;
- sufficiently strong continuation evidence can authorize reversal cancellation and, after a separate positive-geometry gate, a same-direction continuation candidate;
- approximately seven of ten events remain explicit abstentions.

Continuation prediction is materially stronger than reversal prediction, but continuation trading is not inferred automatically. It must pass its own entry, invalidation and target geometry study.

## Authorization

Phase A authorizes two independent next studies:

1. staged reversal execution using only frozen out-of-fold T2 decisions;
2. positive continuation geometry using only frozen out-of-fold T2 continuation decisions.

It also authorizes the independently preregistered extended-reversal target-model study.

The studies must remain separate until each survives its own development and protected-period gates. No 2020–2025 data, Pine, alerts or deployment is authorized by this decision.
