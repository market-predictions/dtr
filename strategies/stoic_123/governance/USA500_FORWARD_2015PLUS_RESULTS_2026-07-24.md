# USA500 RTH Full 1-2-3 Forward Results — 2015+

Date: 2026-07-24  
Work package: `STOIC123-WP-20260724-06`  
Decision: `REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`

## Frozen hypothesis

The study transferred one unchanged candidate from the earlier USA500 screen:

- Dukascopy `USA500IDXUSD` BID M1 proxy, not CME ES futures;
- full 1-2-3 sequence;
- long-only;
- no map;
- no EMA200 filter;
- 5-minute execution and 15-minute management;
- RTH entries from 09:30 inclusive through 16:00 exclusive in `America/New_York`;
- full-session stops, maximum-hold exits and both-direction technical management;
- next-open execution, one-tick baseline slippage and USD 2.25 commission per side.

No parameter, session or filter change was made after preregistration.

## Source qualification

Source-only workflow `30082453148` qualified twelve annual partitions before returns were inspected. Final workflow `30083576930` reacquired every partition and reproduced all frozen SHA-256 values.

- 2015–2019: 1,216,158 active one-minute rows.
- 2020–2022: 1,011,346 rows.
- 2023–2025: 1,006,390 rows.
- 2026 YTD through 2026-07-23: 191,015 rows.
- Total: 3,424,909 rows.
- Duplicate timestamps: zero in every annual partition.

## Results

| Partition | Trades | Net R | Expectancy | Profit factor | Max DD | Return/DD |
|---|---:|---:|---:|---:|---:|---:|
| 2015–2019 primary forward | 177 | **−57.98R** | **−0.328R** | 0.626 | 61.43R | −0.94 |
| 2020–2022 crisis/regime | 134 | +3.12R | +0.023R | 1.032 | 16.06R | 0.19 |
| 2023–2025 recent holdout | 148 | +10.55R | +0.071R | 1.109 | 15.37R | 0.69 |
| **2015–2025 combined** | **459** | **−44.31R** | **−0.097R** | **0.873** | **70.46R** | **−0.63** |
| 2026 YTD monitoring only | 29 | +4.27R | +0.147R | 1.268 | 5.87R | 0.73 |

### Annual breadth

Positive years: 2016, 2022, 2024 and 2025.  
Negative years: 2015, 2017, 2018, 2019, 2020, 2021 and 2023.

The primary forward block had only one positive year out of five. The combined decision period had four positive years out of eleven.

### Uncertainty

- 2015–2019 95% date-block interval: **[−0.586R, −0.051R]**.
- 2020–2022: [−0.273R, +0.339R].
- 2023–2025: [−0.217R, +0.379R].
- 2015–2025 combined: [−0.260R, +0.076R].
- 2026 YTD: [−0.408R, +0.843R].

The primary forward interval is wholly below zero. The positive later blocks remain statistically indeterminate.

### Cost and delay stress

2015–2019:

- two-tick slippage: −87.20R, −0.493R expectancy;
- one-minute delay: −57.79R, −0.330R;
- five-minute delay: −62.70R, −0.399R.

2020–2022 was slightly positive at baseline but negative under doubled slippage and both delays. 2023–2025 remained positive under delays but became negative under doubled slippage at −1.22R.

### Matched controls

The full sequence failed its matched-time control in every partition. The primary candidate expectancy was below even the matched-control 95th percentile. Later matched comparisons either failed superiority or were not holding-period comparable.

### Mechanism diagnostics

EMA-break-only and EMA-break-plus-retest were diagnostic arms and were not eligible for selection. Both were deeply negative in 2015–2019. Their small later-period improvements do not authorize a post-hoc replacement.

## Gates

Six of nineteen frozen gates passed. The candidate failed:

- primary expectancy and confidence;
- primary annual breadth and concentration;
- primary cost and delay robustness;
- primary drawdown and return/drawdown;
- primary matched control;
- crisis annual breadth;
- recent two-tick cost stress;
- combined expectancy and return/drawdown.

## Interpretation

The positive 2012–2014 USA500 observation did not survive broad forward history. Performance improved again during 2022 and 2024–2026, but selecting only those years would be retrospective regime cherry-picking. The unchanged candidate is negative over the complete 2015–2025 decision window and cannot be promoted.

## Decision

`REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`

Do not purchase actual ES data, build a Pine strategy, optimize the RTH window, add EMA200, or tune stops, targets, weekdays, volatility or regimes for this formulation. The mechanical Stoic 1-2-3 family remains closed without a finalist.
