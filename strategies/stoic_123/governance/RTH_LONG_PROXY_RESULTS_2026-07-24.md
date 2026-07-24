# RTH Long Proxy Validation — Final Results

Date: 2026-07-24
Work package: `STOIC123-WP-20260724-04`
Workflow run: `30055431023`
Artifact SHA-256: `fd8efe72387c194cc49fe9734bea38ba9e65cde66c96bdaa1b679e8dd7af67e6`
Decision: `REJECT_RTH_LONG_PROXY_HYPOTHESIS_NO_ACTUAL_NQ_VALIDATION`

## Research question

The prior actual-NQ validation showed a post-hoc improvement when long entries were restricted to regular trading hours. This package froze one canonical session definition and tested whether the effect reproduced on previously uninspected Dukascopy USATECH proxy history, and whether a simple EMA break was superior to the full Stoic 1-2-3 sequence.

The fixed entry window was `09:30:00` inclusive through `16:00:00` exclusive in `America/New_York`, with IANA daylight-saving rules. Only entries were filtered. Stops, opposite-direction technical exits and maximum-hold management remained active around the clock.

## Source boundary

Source-only qualification occurred before performance execution:

- 2012-2013: fresh history, 286,705 active one-minute rows;
- 2014: untouched holdout, 316,579 rows;
- 2010: unavailable;
- 2011: rejected as an insufficient one-week fragment.

Every executed partition matched its frozen compressed-file checksum and contained zero duplicate timestamps. The source remains a Dukascopy bid-CFD proxy, not CME NQ futures.

## Primary result — RTH EMA break long-only

| Partition | Trades | Net R | Expectancy | Profit factor | Max DD | Date-block 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| 2012-2013 fresh history | 858 | `-30.35R` | `-0.035R` | 0.960 | 106.95R | `[-0.275R, +0.293R]` |
| 2014 holdout | 522 | `-104.84R` | `-0.201R` | 0.743 | 108.76R | `[-0.340R, -0.051R]` |

Annual fresh-history attribution was negative in both years:

- 2012: `-30.08R`;
- 2013: `-0.26R`.

The 2014 holdout interval was entirely below zero. The primary hypothesis therefore failed both economically and statistically on the untouched holdout.

## Robustness — RTH EMA break

Fresh history:

- two-tick stress: `-137.68R`, `-0.160R` expectancy;
- one-minute delay: `-52.03R`, `-0.063R` expectancy;
- five-minute delay: `-20.34R`, `-0.026R` expectancy.

Holdout:

- two-tick stress: `-154.94R`, `-0.297R` expectancy;
- one-minute delay: `-103.15R`, `-0.202R` expectancy;
- five-minute delay: `-104.10R`, `-0.220R` expectancy.

The result did not survive baseline execution, let alone stress.

## Secondary result — full RTH 1-2-3 long-only

| Partition | Trades | Net R | Expectancy | Profit factor | Max DD | Date-block 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| 2012-2013 fresh history | 76 | `-13.31R` | `-0.175R` | 0.764 | 25.71R | `[-0.527R, +0.224R]` |
| 2014 holdout | 49 | `-11.24R` | `-0.229R` | 0.632 | 17.35R | `[-0.542R, +0.124R]` |

The full sequence underperformed the simpler EMA-break model by:

- `-0.140R` expectancy per trade on fresh history;
- `-0.029R` expectancy per trade on the holdout.

It therefore failed the incremental-mechanism gate. The sequence reduced trade count and drawdown but did not create positive expectancy.

## Diagnostic retest result

The EMA-break-plus-retest diagnostic was also negative:

- fresh history: 770 trades, `-38.18R`, `-0.050R` expectancy;
- holdout: 462 trades, `-73.86R`, `-0.160R` expectancy.

The retest requirement did not rescue the long thesis.

## Session interpretation

Restricting full-sequence entries to RTH reduced losses relative to broader entry sets, particularly on the 2014 holdout:

- full-session full sequence: `-42.28R`;
- overnight-entry full sequence: `-31.50R`;
- RTH-entry full sequence: `-11.24R`.

This supports a descriptive claim that RTH filtering can reduce adverse exposure. It does not establish a positive trading edge. A loss reduction is not equivalent to a profitable mechanism.

## Matched-time controls

Fifty deterministic RTH matched-time controls were run for both candidates in each partition.

- EMA break achieved 99.24%-100% event coverage and comparable holding periods, but candidate expectancy failed to exceed matched-control p95 in both partitions.
- Full sequence achieved full event coverage, but holding-period ratios were outside the frozen comparability range and candidate expectancy failed matched-control p95 in both partitions.

Neither candidate demonstrated sequence- or timing-specific alpha.

## Gate result

Only two of seventeen gates passed:

- fresh-history EMA-break trade count at least 250;
- holdout EMA-break trade count at least 75.

Every expectancy, uncertainty, annual breadth, cost, delay, risk-adjusted return, holdout and matched-control gate failed. All four secondary gates failed.

## Final decision

`REJECT_RTH_LONG_PROXY_HYPOTHESIS_NO_ACTUAL_NQ_VALIDATION`

- Do not purchase or acquire additional actual-NQ data for this current RTH long formulation.
- Do not tune the RTH window, opening period, lunch hours, weekdays, volatility, EMA lengths, stops, targets, delays, timeframes or exits on these samples.
- Do not select the retest diagnostic or another descriptive comparator from the same artifact.
- Do not port the family to Pine or authorize alerts, sizing, paper deployment or live trading.

The earlier positive RTH attribution did not transfer to fresh proxy history. The current mechanical Stoic family remains closed without a finalist.
