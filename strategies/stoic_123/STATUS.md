# Status — Stoic Edge 1-2-3

Date: 2026-07-24  
Version: `v0.8.0-research-platform`  
Active work package: none  
Strategy decision state: `REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`  
Platform state: `RESEARCH_CYCLE_ACCELERATION_COMPLETE`

## Strategy evidence state

The current mechanical Stoic Edge 1-2-3 research family is complete and closed without a finalist.

Completed evidence includes:

- separate causal namespace, governance tree, execution engine and frozen phase-one family;
- qualified NQ futures, NQ proxy, USA500 proxy and GBPUSD source contracts;
- corrected entry-direction restrictions while retaining opposite-direction technical management;
- actual-NQ long-only validation;
- unseen short-side proxy falsification;
- fresh-history RTH long validation on USATECH;
- USA500 cross-asset screen;
- full USA500 forward validation from 2015 through 2025 plus 2026 YTD monitoring;
- cost, delay, uncertainty, annual, exit, matched-control and independent-reconstruction checks.

## Final USA500 forward result

Frozen candidate: USA500 RTH full 1-2-3, no-map, long-only, no EMA200.

| Partition | Trades | Net R | Expectancy | Max DD |
|---|---:|---:|---:|---:|
| 2015–2019 | 177 | −57.98R | −0.328R | 61.43R |
| 2020–2022 | 134 | +3.12R | +0.023R | 16.06R |
| 2023–2025 | 148 | +10.55R | +0.071R | 15.37R |
| **2015–2025 combined** | **459** | **−44.31R** | **−0.097R** | **70.46R** |
| 2026 YTD monitoring | 29 | +4.27R | +0.147R | 5.87R |

The 2015–2019 confidence interval was wholly negative. Only one of five primary years and four of eleven combined years were positive. Doubled-cost and matched-time controls failed. Six of nineteen gates passed.

## Independent strategy verification

- 45/45 ledgers reconstructed exactly.
- Zero metric, chronology, risk, overlap, RTH-classification, source-contract, annual-attribution or gate-reconstruction failures.
- All 19 gate outcomes reproduced.
- Both management directions remained active.
- Raw source data were removed before compact artifact publication.

## Research platform acceleration

Completed work packages:

- `STOIC123-WP-20260724-07` — staged execution, caching, exact cost repricing and profiling;
- `STOIC123-WP-20260724-08` — four-way parallel certification and deterministic aggregation;
- `STOIC123-WP-20260724-09` — discovery-only batch variation infrastructure.

Operational modes:

| Mode | Purpose | Can promote? |
|---|---|---:|
| `screen` | Fast rejection on designated discovery data | No |
| `validate` | Robustness testing for survivors | No |
| `certify` | Complete retain/hold/reject decision | Yes |
| `legacy` | Former full path retained for parity | Yes, under its frozen contract |

Measured real-data performance:

| Cycle | Wall time |
|---|---:|
| Cold-cache screen | 9.81s |
| Warm-cache screen | 4.54s |
| Staged validation with futility rejection | 5.58s |
| Full accelerated sequential certification | 52.56s |
| Parallel certification compute lower bound | 21.45s |

Parallel partition compute was `2.85x` faster than the serial partition sum. Accelerated candidate summaries reproduced the frozen reference within `1e-12`; all 19 gates and the final strategy decision matched exactly.

The profiler showed matched controls as the dominant certification cost. Ordinary simulation was not dominant, so Numba/GPU work is deferred to avoid unsupported complexity.

## Scientific strategy decision

`REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`

The positive 2012–2014 USA500 screen did not survive broad 2015–2025 forward history. Positive results in 2024–2026 cannot be selected retrospectively as a new regime without a genuinely new preregistered mechanism and new unseen data.

## Platform use boundary

- Fast modes may reject candidates but cannot promote them.
- Batch screening is discovery-only and cannot access holdout partitions.
- A survivor must be frozen before validation and certification.
- Final certification retains source hashes, one-minute execution, complete gates and independent reconstruction.
- Platform acceleration does not authorize another sweep of the closed Stoic family.

## Restrictions

- No DTR or Asian Sweep result is changed.
- No Stoic direction, threshold, timeframe, session subdivision, weekday, month, volatility, regime, EMA200, stop, target, delay, matching-rule or exit optimization.
- No candidate may be selected from inspected diagnostics or recent-year subsets.
- No paid actual-ES or actual-NQ acquisition for this formulation.
- No proxy result may be represented as CME futures evidence.
- No Pine, sizing, alert, paper-trading, deployment or profitability authorization.
