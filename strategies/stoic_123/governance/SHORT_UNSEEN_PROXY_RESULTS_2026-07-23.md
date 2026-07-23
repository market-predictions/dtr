# Stoic Short-Side Unseen Proxy Falsification — Final Results

Date: 2026-07-23
Work package: `STOIC123-WP-20260723-03`
Workflow run: `30047912422`
Artifact SHA-256: `324849b9ae7958f13f426dc0f12763b118e2f2ffe2add827ab2a4d93ab840418`
Decision: `REJECT_CURRENT_SHORT_SIDE_HYPOTHESIS_NO_PAID_NQ_VALIDATION`

## Research question

The previous actual-NQ validation exposed a strong no-map short-only result after the fact. Because that observation was post-hoc, this package froze it as one unchanged hypothesis and challenged it only on disjoint Dukascopy USATECH bid-CFD proxy partitions:

- older history: 2015-01-01 through 2021-12-31;
- fresh proxy check: 2026-01-01 through 2026-07-22.

The inspected 2022-12-26 through 2025-12-10 NQ sample and 2022-2025 USATECH performance were excluded.

## Source integrity

- Eight deterministic annual/YTD source partitions were qualified before performance execution.
- Every partition was reacquired and checked against its frozen SHA-256 during the final workflow.
- Combined older-history rows: `1,998,563`.
- Forward-2026 rows: `189,836`.
- Duplicate timestamps: `0`.
- No source row overlapped the inspected NQ sample.
- Source classification remained: Dukascopy USATECH bid-CFD proxy, not CME NQ futures.
- Raw source files were removed before result-artifact upload.

## Primary short-only result

| Partition | Trades | Net R | Expectancy | PF | Max DD | Date-block 95% interval |
|---|---:|---:|---:|---:|---:|---:|
| 2015-2021 | 696 | -86.13R | -0.124R | 0.876 | 167.56R | [-0.412R, +0.209R] |
| 2026 YTD | 43 | +2.12R | +0.049R | 1.059 | 11.52R | [-0.672R, +0.914R] |

The older unseen partition rejects the hypothesis. Only two of seven years were positive:

- 2015: `-9.25R`;
- 2016: `+25.12R`;
- 2017: `-55.08R`;
- 2018: `-9.57R`;
- 2019: `-62.90R`;
- 2020: `-0.57R`;
- 2021: `+26.12R`.

The positive-year concentration was `50.98%`, above the frozen `40%` limit.

## Cost and delay stress

On 2015-2021:

- two-tick slippage: `-142.73R`, `-0.205R` expectancy;
- one-minute delay: `-102.16R`, `-0.149R` expectancy;
- five-minute delay: `-117.15R`, `-0.179R` expectancy.

On 2026 YTD:

- two-tick slippage remained slightly positive at `+1.33R`, but its interval remained extremely wide;
- one-minute delay returned `+1.81R`;
- five-minute delay returned `+6.77R`.

These small forward observations do not offset the negative seven-year result and are not authorization to optimize entry delay.

## Mechanism controls

The full short 1-2-3 sequence did not demonstrate incremental mechanism value:

- 2015-2021 short EMA-break-only expectancy: `-0.125R`;
- full-sequence gain over EMA break: only `+0.001R`;
- 2026 YTD short EMA-break-only expectancy: `+0.080R`;
- full sequence underperformed it by `-0.031R`.

The sequence therefore adds complexity without reproducible incremental edge.

## Matched-time controls

Fifty deterministic short matched-time controls were executed per partition.

- Older history achieved `99.73%` minimum event coverage and a comparable `1.139` holding-period ratio, but full expectancy did not exceed matched-control p95 (`+0.165R`).
- Forward 2026 achieved `100%` event coverage, but its holding-period ratio was only `0.634`, outside the frozen comparability range, and full expectancy did not exceed matched-control p95 (`+0.471R`).
- Both matched-control gates failed.

## Promotion screen

Only four of twelve gates passed:

- older-history trade count at least 500;
- forward-2026 trade count at least 30;
- forward-2026 expectancy positive;
- forward-2026 two-tick expectancy positive.

The hypothesis failed older expectancy, uncertainty, year breadth, concentration, cost stress, delayed-entry robustness, mechanism value, and matched-time control gates.

## Final decision

`REJECT_CURRENT_SHORT_SIDE_HYPOTHESIS_NO_PAID_NQ_VALIDATION`

- Do not purchase new actual-NQ data for this current mechanical short formulation.
- Do not tune direction, sessions, weekdays, maps, stops, targets, delays, timeframes, exits, or matching rules on these samples.
- Do not pivot to the descriptive long comparator from the same artifact.
- Do not port this family to Pine or authorize sizing, alerts, paper deployment, or live trading.
- Close the current mechanical Stoic 1-2-3 research family.

A future Stoic project is justified only by a genuinely different, independently motivated market mechanism that is preregistered before new performance inspection.
