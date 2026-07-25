# Final Decision — Asian Sweep Ten-Pair FX Discovery

Date: 2026-07-25  
Work package: `AS-WP-20260725-10`  
Workflow run: `30149721151`  
Decision: `FAIL_DISCOVERY_STOP_BEFORE_MECHANISM_VALIDATION`

## Executive conclusion

The causally confirmed London rejection of the completed Asian range did **not** add a positive reversal effect relative to matched non-rejection boundary breaches across the fixed ten-pair FX universe.

The pattern was frequent and broadly observable, but the pooled control-adjusted effect was negative, its clustered uncertainty interval included zero, the one-sided permutation result strongly rejected a positive-evidence interpretation, and cross-pair/factor breadth failed. Under the preregistered rules, 2020–2021 mechanism validation and all executable strategy work remain unauthorized.

This is a mechanism rejection, not an execution-backtest failure. No entry, stop, target, spread cost, slippage, R multiple or strategy P&L was calculated.

## Frozen research object

Universe:

- EURUSD, GBPUSD, USDCHF;
- AUDUSD, NZDUSD, USDCAD;
- USDJPY, EURJPY, GBPJPY;
- EURGBP.

Discovery period: 2015–2019 only.

Primary event: the unchanged causal Asian Sweep auction-state detector classified the first London Asian-range breach as `REJECTION`.

Primary endpoint: reversal-signed midpoint return over the next 60 minutes, capped at the London-window end, divided by completed Asian-range width.

Controls: five non-rejection first-boundary events on distinct dates, exactly matched within pair/year/weekday/30-minute confirmation bucket and deterministically nearest-matched on causal Asian-range percentile and breach depth.

Inference: 10,000 calendar-date block-bootstrap iterations and 10,000 calendar-date clustered sign permutations.

## Primary results

| Metric | Result |
|---|---:|
| Matched rejection events | 2,498 |
| Matched controls | 12,490 |
| Independent London dates | 1,104 |
| Mean rejection-event return | `+0.005890` Asian-range fractions |
| Mean matched-control return | `+0.024507` Asian-range fractions |
| **Mean event-minus-control effect** | **`-0.018617` Asian-range fractions** |
| 95% date-block interval | `[-0.046224, +0.008483]` |
| Bootstrap probability effect > 0 | `0.0888` |
| One-sided clustered permutation p-value | `0.910809` |
| Positive pair estimates | `4 / 10` |
| Positive factor-block estimates | `1 / 4` |
| Maximum pair share | `14.45%` |
| Maximum date share | `0.28%` |

Interpretation: the event group showed a very small raw reversal, but matched non-rejection breaches reversed more. The confirmed-rejection state therefore did not isolate incremental reversal value.

## Pair attribution

| Pair | Events | Mean effect |
|---|---:|---:|
| AUDUSD | 163 | `+0.006742` |
| EURGBP | 361 | `-0.008358` |
| EURJPY | 226 | `+0.004469` |
| EURUSD | 330 | `+0.002851` |
| GBPJPY | 234 | `-0.029884` |
| GBPUSD | 325 | `-0.029880` |
| NZDUSD | 169 | `+0.028808` |
| USDCAD | 242 | `-0.004542` |
| USDCHF | 316 | `-0.103749` |
| USDJPY | 132 | `-0.006202` |

The four positive pairs may not be selected retrospectively. Only NZDUSD exceeded the pooled effect threshold individually, and that observation has no promotion authority.

## Factor-block attribution

| Factor block | Events | Mean effect |
|---|---:|---:|
| Europe cross | 361 | `-0.008358` |
| JPY | 592 | `-0.011489` |
| USD commodity | 574 | `+0.008481` |
| USD Europe | 971 | `-0.042796` |

Only one factor block was positive, and its point estimate remained below the required `+0.02` threshold.

## Annual attribution

| Year | Events | Mean effect |
|---|---:|---:|
| 2015 | 514 | `-0.023789` |
| 2016 | 466 | `-0.010622` |
| 2017 | 569 | `-0.037842` |
| 2018 | 492 | `-0.038384` |
| 2019 | 457 | `+0.024264` |

Four of five discovery years were negative. The sole positive year cannot rescue the pooled mechanism.

## Frozen gate result

Passed:

1. at least 400 matched events;
2. at least eight pairs with at least 20 events;
3. all four factor blocks with at least 40 events;
4. no pair above 25% of the pool;
5. no date above 10% of the pool.

Failed:

1. mean effect at least `+0.02`;
2. positive 95% bootstrap lower bound;
3. one-sided permutation p-value at most 0.05;
4. at least seven positive pairs;
5. at least three positive factor blocks.

Result: `5 / 10` predicates passed. Every effect and statistical-evidence predicate failed.

## Independent reconstruction

The preserved ledgers were independently reconstructed outside GitHub Actions. The audit confirmed:

- 2,498 unique matched event IDs;
- exactly five controls per event;
- five distinct control dates per event;
- zero same-date event/control leakage;
- correct pair identity for every event and control;
- event/control mean and effect arithmetic to machine precision;
- exact pair and factor attribution;
- 1,104 date blocks and concentration calculations;
- the 10,000-iteration bootstrap to floating-point precision;
- the 10,000-iteration clustered permutation result exactly;
- every frozen gate decision.

No evidence of source, matching, arithmetic or inference failure was found.

## Evidence provenance

- Qualified source-artifact run: `30111481052`.
- Discovery workflow run: `30149721151`.
- Decision artifact: `asia-sweep-fx-discovery-decision`.
- Decision artifact digest: `sha256:9f0dd7f498e5621d72629e0dba7405a554656024c46c738cb4a0499788c689cd`.
- Pooled matched-event ledger SHA-256: `9f2c2c31c2a7ad2718b59bf6524b10be983402a74a0c3ef1945e3daff6451e2a`.
- Decision JSON SHA-256: `c8c17fa9e1bde399c5cdbc1735c91f8395ef5ea8bcb4db3def8533ca004d71ac`.

All ten pair artifacts remain retained for 90 days from the discovery run.

## Disposition

- Do not open 2020–2021 mechanism-validation returns.
- Keep 2022–2023 executable validation blocked.
- Keep 2024–2025 untouched.
- Do not optimize the session clock, confirmation state, endpoint, controls or thresholds after seeing this result.
- Do not select NZDUSD or the four positive pairs as a rescue basket.
- Do not revive AS-A through AS-D or the PDH/PDL cluster as hidden variants of this trial.
- Do not build Pine, alerts, sizing, paper trading or deployment from this formulation.

A future Asian-session research programme requires a genuinely new economic hypothesis, new preregistration and new unseen evidence. It cannot be presented as continuation or optimization of this failed discovery trial.
