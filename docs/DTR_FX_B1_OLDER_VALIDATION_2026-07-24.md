# DTR-FX B1 older-history validation

Date: 2026-07-24  
Work package: `DTR-FX-WP-20260724-23`  
Instrument/data: Dukascopy GBPUSD M1 BID/ASK

## Decision

`REJECT_B1_ON_OLDER_HISTORY`

The frozen B1 contract is **rejected as a GBPUSD strategy candidate**. Aggregate expectancy was positive, but the preregistered temporal-consistency gate failed: only 3 of 7 years were positive. The date-block confidence interval also crosses zero. No parameter rescue, selective direction filter, Pine conversion, sizing, paper deployment, or live use is authorized.

## Frozen validation result: 2015-2021

- Trades: 105
- Net result: 10.336779R
- Net expectancy: 0.098446R/trade
- Gross expectancy: 0.171485R/trade
- Profit factor: 1.187675
- Win rate: 44.76%
- Maximum drawdown: 14.327014R
- Return/max-drawdown: 0.721489
- Expectancy at 1.5x execution cost: 0.053032R/trade
- Primary 2015-2019 expectancy: 0.011409R/trade
- Crisis extension 2020-2021 expectancy: 0.326542R/trade
- Date-block 95% interval: [-0.158471, 0.359370]R/trade
- Bootstrap probability of positive expectancy: 0.766

## Annual decomposition

| Year | Trades | Net R | Expectancy R |
|---:|---:|---:|---:|
| 2015 | 17 | 8.365434 | 0.492084 |
| 2016 | 16 | -3.941889 | -0.246368 |
| 2017 | 13 | 4.111509 | 0.316270 |
| 2018 | 16 | -1.272288 | -0.079518 |
| 2019 | 14 | -6.395719 | -0.456837 |
| 2020 | 10 | -0.467681 | -0.046768 |
| 2021 | 19 | 9.937412 | 0.523022 |

The positive total is dominated by 2015 and 2021. Four years were negative, including three consecutive weak years from 2018 through 2020. The 2015-2019 primary partition was effectively flat at 0.011409R/trade. Maximum drawdown exceeded total net R, which is inconsistent with a stable, deployable edge.

## Preregistered gates

| Gate | Result |
|---|---|
| Combined expectancy > 0 | PASS |
| 1.5x-cost expectancy > 0 | PASS |
| 2015-2019 expectancy > 0 | PASS, marginal |
| 2020-2021 expectancy > 0 | PASS |
| At least 4 of 7 positive years | **FAIL: 3 of 7** |
| No single year > 60% of positive net R | PASS |
| Date-block CI lower bound > 0 | **FAIL** |

The hard-stop decision is therefore `REJECT_B1_ON_OLDER_HISTORY`.

## Source and execution integrity

- Full UTC minute grid: 3,682,080 rows
- Active synchronized BID/ASK minutes: 2,612,846
- Duplicate timestamps: 0
- Negative spread rows: 0
- Median active spread: 0.90 pip
- 75th-percentile active spread: 1.10 pips
- Frozen London spread gate: 1.20 pips
- Runner SHA-256: `8bed9d9e0d7e198ff5a3d8f02cc8f4303ace7d1820885fcde13bcb5774a81e59`
- Trade ledger SHA-256: `ea2fff239a4707315b4a4cfdfd7398808dbf2177f99ab52aa5f4c1ec91d269e3`
- Independent ledger reconstruction: `PASS`
- Metric mismatches: 0

## Interpretation

The result shows a **weak, episodic mechanism**, not a sufficiently consistent GBPUSD strategy. Positive aggregate R is not enough: the edge disappears across long multi-year blocks and is too dependent on isolated strong years. The earlier 2022-2025 research result (+9.686R over 55 trades) therefore does not justify promotion when tested against older, source-qualified history.

## Roadmap decision

Close the current DTR-FX/B1 line as a deployable-strategy candidate. Retain it only as a documented benchmark for future independent FX research. Any further GBPUSD work should begin as a separate, preregistered strategy family based on an independently motivated FX edge rather than post-hoc modifications to B1.
