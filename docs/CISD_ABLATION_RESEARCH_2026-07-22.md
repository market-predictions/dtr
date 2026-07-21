# NQ CISD Entry-Confirmation Ablation — 2026-07-22

## Decision

`REJECT_NO_INCREMENTAL_VALUE`

Causal Change in State of Delivery (CISD) confirmation does not improve the frozen 491-trade NQ gap-safe reversal strategy as an implementable hard filter. The detector and annotations are retained for diagnostics and reproducibility only.

## Research question

Does a causal close through the open of the latest opposite-delivery sequence add independent decision value to the existing reversal entry after opportunity loss and portfolio sequencing are accounted for?

Two explicit anchors were tested:

1. **Sequence anchor:** open of the first candle in the newest contiguous opposite-delivery sequence after the sweep.
2. **Last-candle anchor:** open of the final candle in that same sequence.

For bullish reversals, opposite delivery is bearish candle bodies and confirmation is a later close above the anchor. Bearish logic is symmetric. The start of a newer opposite-delivery sequence expires every older sequence, including one that confirmed earlier. Reset epochs invalidate all prior state.

## Data and execution contract

- Dataset SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Decision bars: five minutes.
- Execution bars: one minute.
- Gap policy: `reject_unsafe`.
- Frozen reversal parameters: unchanged.
- Baseline slippage: one tick each side.
- Commission: USD 2.25 each side.
- Same-minute collision policy: conservative stop first.

## Frozen baseline

| Trades | Expectancy | Net R | Profit factor | Max drawdown | Return/DD |
|---:|---:|---:|---:|---:|---:|
| 491 | 0.180236R | 88.495783R | 1.381998 | 14.107858R | 6.272801 |

The observe variant reproduced the frozen baseline exactly.

## Implementable portfolio results

| Variant | Trades | Coverage | Expectancy | Net R | PF | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|---:|---:|
| Observe | 491 | 100.0% | 0.180236R | 88.495783R | 1.381998 | 14.107858R | 6.272801 |
| Sequence confirm | 309 | 62.9% | 0.144100R | 44.526769R | 1.301041 | 9.973118R | 4.464679 |
| Last-candle confirm | 309 | 62.9% | 0.144100R | 44.526769R | 1.301041 | 9.973118R | 4.464679 |
| Sequence recent ≤3 | 296 | 60.3% | 0.136305R | 40.346368R | 1.282502 | 9.176643R | 4.396637 |
| Sequence recent ≤6 | 309 | 62.9% | 0.140105R | 43.292439R | 1.290711 | 9.973118R | 4.340913 |
| Sequence retest | 75 | 15.3% | 0.256552R | 19.241391R | 1.581671 | 5.160423R | 3.728646 |

Broad CISD confirmation is clearly inferior to the baseline. The sequence and last-candle anchors produce the same qualifying set in this dataset, so the anchor neighbourhood offers no independent robustness evidence.

## Cohort versus implementable filtering

The frozen baseline contains 73 trades with a causal sequence retest:

- coverage: 14.87%;
- expectancy: 0.291543R;
- net: 21.282645R;
- complement expectancy: 0.160797R;
- point-estimate uplift: 0.130746R.

The implementable filter produces 75 trades because removing earlier trades changes position occupancy and enables two later trades. Those added trades lose 2.041254R in total, reducing expectancy to 0.256552R.

Broad sequence confirmation removes 186 baseline trades whose combined result is +43.145942R and enables four later trades whose combined result is -0.823072R. This is the opposite of useful selection.

## Chronological retest evidence

The 73-trade frozen retest cohort is positive in each main period:

| Period | Retest trades | Retest expectancy | Complement expectancy |
|---|---:|---:|---:|
| Development | 32 | 0.318362R | 0.177123R |
| Validation | 21 | 0.222364R | 0.158311R |
| Later research | 20 | 0.321270R | 0.148446R |

However, the timing decomposition is unstable:

- entry-bar retests are strong in development and validation but nearly flat later;
- retests occurring before the entry bar are weak in development and validation but positive later.

The aggregate result therefore combines subgroups whose period behaviour does not share a stable mechanism.

## Incremental uncertainty

For the retest cohort versus its complement:

- trade-bootstrap 95% uplift interval: `[-0.185467R, 0.456152R]`;
- month-block bootstrap 95% uplift interval: `[-0.102844R, 0.382941R]`;
- one-sided permutation p-value: `0.210289`.

The absolute retest expectancy is positive, but the incremental uplift over the already-positive baseline is not statistically established.

## Cost stress

The retest portfolio remains positive under two- and four-tick slippage, but its return-to-drawdown remains below the frozen baseline at every cost level:

| Slippage each side | Baseline expectancy | Baseline return/DD | Retest expectancy | Retest return/DD |
|---:|---:|---:|---:|---:|
| 1 tick | 0.180236R | 6.272801 | 0.256552R | 3.728646 |
| 2 ticks | 0.160757R | 5.341525 | 0.246849R | 3.489597 |
| 4 ticks | 0.144529R | 4.297075 | 0.248523R | 3.338792 |

Cost survival is encouraging for the absolute subset, but it does not repair the lower portfolio efficiency or uncertainty of the incremental uplift.

## Determinism and implementation review

- causal bullish and bearish fixtures pass;
- sequence and last-candle anchors are explicit;
- confirmation cannot occur before sequence completion;
- a newer sequence expires older unconfirmed and confirmed state;
- reset epochs invalidate pre-reset state;
- strict manifest validation and dataset checksum verification pass;
- every removed and newly enabled trade is attributed;
- two clean canonical runs produced 52 of 52 byte-identical artifacts;
- frozen reversal parameters and baseline remain unchanged.

## Independent conclusion

1. Broad CISD confirmation reduces expectancy and return-to-drawdown.
2. Recent confirmation does not improve the result.
3. Sequence and last-candle anchors are empirically redundant in this sample.
4. A post-confirmation retest identifies a higher-expectancy descriptive cohort.
5. The cohort is too small and its incremental uplift too uncertain for a filter or sizing rule.
6. Hard filtering discards substantial positive baseline return and enables later losing trades.

Decision: `REJECT_NO_INCREMENTAL_VALUE`.

The CISD detector may remain as a diagnostic annotation. No CISD filter, sizing rule, combination search, production deployment, or Pine implementation is authorized on the current NQ sample.
