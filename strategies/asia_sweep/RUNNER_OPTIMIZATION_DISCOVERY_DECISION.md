# Asian Sweep Runner Optimisation — Discovery Decision

Date: `2026-07-26`  
Actions run: `30195612634`  
Evaluated head: `422a70bd85fa7021aa72d10f38281873bdb2c652`  
Decision artifact: `sha256:aad7718b2a97be9ffef19ace69eaed1a1ac14051f2f90aac70e7ab0bf683f323`

## Decision

`FAIL_RUNNER_DISCOVERY_STOP_BEFORE_VALIDATION`

No stable longer-horizon runner policy passed the frozen leave-one-year-out discovery gate. The 2020–2025 runner partitions remain unopened.

This does not block a separately preregistered earlier-entry hypothesis. It blocks combining earlier entry with a runner policy selected from this failed grid.

## Frozen search

- exact validated T5 signal and threshold;
- exact audited market-next-open entries;
- 50% at Asian midpoint TP1;
- 50% runner;
- TP1 allowed at any time before the policy horizon;
- targets: 2R, 3R, 4R, 5R, or opposite Asian boundary;
- exits: 12:00, 14:00, 16:00, or 18:00 Amsterdam;
- original stop or break-even from the first active minute after TP1;
- 40 policies;
- nested leave-one-year-out selection on 2015–2019.

## Nested out-of-fold result

Only two of five outer folds found any policy satisfying the inner requirements of positive performance on both pairs and at least three of four inner years.

| Outer year | Inner-selected policy | Held-out expectancy | 0.10-pip stress |
|---|---|---:|---:|
| 2015 | none | — | — |
| 2016 | none | — | — |
| 2017 | `4R_H14_BREAK_EVEN_AFTER_TP1` | `-0.13025R` | `-0.14987R` |
| 2018 | `4R_H12_BREAK_EVEN_AFTER_TP1` | `-0.02132R` | `-0.04221R` |
| 2019 | none | — | — |

Combined out-of-fold evidence:

- trades: `252`;
- net: `-18.92465R`;
- expectancy: `-0.07600R`;
- 0.10-pip stress: `-0.09626R`;
- maximum drawdown: `20.41049R`;
- bootstrap probability expectancy positive: `14.71%`;
- bootstrap 95% interval: `[-0.21930R, +0.06532R]`;
- EURUSD expectancy: `+0.08039R`;
- GBPUSD expectancy: `-0.23366R`;
- positive outer years: `0 / 2` selected years.

The nested result failed effect, stress, pair breadth, year breadth, stability, bootstrap and return/drawdown gates.

## Modal policy

The tie-broken modal choice was:

`4R_H12_BREAK_EVEN_AFTER_TP1`

It appeared in only one of five folds, so it was not stable.

Full 2015–2019 descriptive metrics:

- trades: `630`;
- net: `+9.62550R`;
- expectancy: `+0.01540R`;
- 0.10-pip stress: `-0.00463R`;
- maximum drawdown: `48.96891R`;
- return/drawdown: `0.19656`;
- bootstrap probability expectancy positive: `62.78%`;
- positive pairs: `1 / 2`;
- positive years: `3 / 5`;
- largest winner: `40.05%` of net R;
- TP1 hit rate: `46.83%`;
- 4R runner-target hit rate: `10.79%`.

Pair attribution:

| Pair | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| EURUSD | `321` | `+22.72123R` | `+0.07078R` |
| GBPUSD | `304` | `-13.09574R` | `-0.04308R` |

Year expectancy:

- 2015: `+0.09556R`;
- 2016: `+0.05104R`;
- 2017: `-0.11717R`;
- 2018: `-0.02132R`;
- 2019: `+0.07143R`.

## Best pooled policy — descriptive only

The strongest pooled policy under 0.10-pip stress was:

`4R_H16_BREAK_EVEN_AFTER_TP1`

- net: `+14.84613R`;
- expectancy: `+0.02375R`;
- 0.10-pip stress: `+0.00392R`;
- maximum drawdown: `49.63682R`;
- positive pairs: `1 / 2`;
- positive years: `3 / 5`;
- EURUSD expectancy: `+0.10075R`;
- GBPUSD expectancy: `-0.05755R`;
- 4R runner-target hit rate: `14.13%`.

It cannot be promoted because it was selected after pooled inspection, lacked pair breadth, failed two consecutive years, and had poor return/drawdown.

## Family-level findings

- 2R runners were uniformly negative; reaching a nearby target did not compensate for stop and time-exit losses.
- 3R and 4R were the only target families approaching positive pooled expectancy.
- 4R with 16:00–18:00 exits captured the strongest runner contribution.
- 5R and opposite-boundary targets reduced hit rate without enough additional payoff.
- break-even generally improved the runner family relative to the original stop, but did not create cross-pair or cross-year stability.
- extending the close from 11:00 to 16:00–18:00 improved descriptive pooled expectancy, confirming that 11:00 was too early for some winners; the improvement was not robust enough to authorize a strategy.

## Independent verification

Confirmed from the retained evidence:

- `25,200` policy rows = `630` fixed entries × `40` policies;
- `40` unique policies;
- zero duplicate event-policy rows;
- exactly `630` rows per policy;
- zero weighted-leg arithmetic discrepancies;
- every out-of-fold trade uses the policy recorded for its held-out year;
- the modal ledger contains only `4R_H12_BREAK_EVEN_AFTER_TP1`;
- JSON metrics exactly reconcile to the CSV evidence.

No signal, entry, policy-manifest, weighting or aggregation discrepancy explains the failed gate.

## Interpretation boundary

This rejects the frozen 50/50 runner grid after complete T5 confirmation. It does not establish that all possible runner methods fail.

It specifically shows that allowing later exits and higher R multiples can improve pooled descriptive performance, but the improvement is unstable across pairs and years and fails nested out-of-fold selection.

## Next research path

Earlier-entry research remains justified because the consistent structural problem is that complete T5 confirmation consumes too much favorable movement before entry.

That work must:

- use causal T0/T1/T2/T3/T5 states;
- freeze a simple payoff geometry independently of this failed runner grid;
- test provisional entry, addition, cancellation and early invalidation;
- retain 2020–2025 as unopened execution evidence;
- receive its own branch, contract and gates.

No runner policy from this discovery may be carried into that programme as if validated.
