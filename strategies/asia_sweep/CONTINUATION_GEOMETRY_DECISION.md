# Asian Sweep Continuation Geometry — Decision

Date: 2026-07-26
Decision: `FAIL_CONTINUATION_GEOMETRY_STOP_BEFORE_EXECUTION_PNL`
Development: EURUSD and GBPUSD, 2015–2019
Protected: 2020–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30204549092`;
- evaluated head: `f1216f207ed41676d1ba5a4e2a396e5a23201aba`;
- decision artifact: `asia-sweep-continuation-geometry-decision`;
- digest: `sha256:519b45da4b685ef45200042ddf7c3dbb2cd18cb36d0e393ea492643671c25a64`.

All scientific tests, both pair ledgers, pooled aggregation and artifact upload completed. Only the deliberate pass-enforcement step failed.

## Result

The passing elastic-net T2 continuation classification is real and broad, but none of the five preregistered same-direction entry/target geometries passed all lift, reward/risk, expected-value and breadth gates.

| Objective | Base hit rate | Selected hit rate | Lift | Median selected R:R | Selected >=1.5R | Median stressed EV proxy | Failed gates |
|---|---:|---:|---:|---:|---:|---:|---|
| 0.25 range by 10:00 | 30.41% | 45.72% | 1.50x | 1.01R | 31.02% | +0.299R | lift, median R:R, R:R breadth |
| 0.50 range by 11:00 | 19.39% | 27.54% | 1.42x | 2.28R | 77.81% | +1.090R | lift |
| 1.00 range by 12:00 | 9.82% | 13.10% | 1.33x | 4.67R | 100.00% | +2.621R | lift, year breadth |
| nearest same-side liquidity by 12:00 | 22.33% | 28.57% | 1.28x | 2.00R | 57.14% | +0.852R | lift |
| fixed 2R by 12:00 | 25.12% | 28.61% | 1.14x | 2.00R | 100.00% | +0.925R | lift |

## Interpretation

The classifier identifies genuine continuation tendency, especially for a nearby range-extension objective. However, the positive continuation class used in Phase A is not sufficiently target-specific:

- the nearest objective has useful outcome lift but insufficient payoff geometry;
- the larger objectives have attractive payoff when reached, but the selected target-rate lift is too small;
- no objective simultaneously provides strong target enrichment and robust executable R:R.

Therefore a high Phase A continuation probability remains authorized as:

- a reversal veto;
- an exit/reduce signal;
- an add blocker.

It is not authorized as a same-direction continuation trade under the tested geometry.

## Integrity audit

The pooled ledger and every objective summary were independently reconstructed. Objective event counts, hit rates, selected rates, lifts, reward/risk distributions, stressed expected-value proxies, pair/year breadth and failed predicates reproduced to floating-point tolerance.

## Closed path

The following continuation formulation is rejected before execution P&L:

- elastic-net T2 continuation decision;
- next active BID/ASK market entry;
- 0.10-range reclaim stop;
- the five frozen objectives above.

No threshold, landmark, stop, target, pair or year rescue is permitted on this branch.

## Next valid use

Continuation classification remains part of the staged reversal architecture as defensive information. A future continuation-trade programme would require a more target-specific continuation model rather than a different target applied to the current broad immediate-continuation classifier.
