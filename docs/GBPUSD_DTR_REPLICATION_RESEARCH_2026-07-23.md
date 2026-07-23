# GBPUSD DTR Replication — 2026-07-23

## Decision

`NO_VIABLE_GBPUSD_DTR_BASELINE`

The frozen Day Trader Rauf core was applied to Dukascopy GBPUSD one-minute bid/ask data from 2022 through 2025. Signals use synchronized midpoint OHLC. The execution model uses the observed 75th-percentile spread, 0.1 pip slippage per side, and a $3.50 commission per side for one standard lot.

## Data audit

- Synchronized active candles: 1,488,142
- Active period: 2022-01-02 17:01 ET through 2025-12-31 16:58 ET
- Median quoted spread: 0.90 pips
- 75th-percentile spread: 1.10 pips
- Base modeled slippage: 0.65 pips per side
- Eligible covered sessions: 3,056
- The source BI5 field order was corrected to `open, close, low, high` before analysis; all corrected annual files passed OHLC integrity.

## Monday × Asia factorial

| Arm | Trades | Net R | Expectancy | +1 pip each side | Max DD | Positive years |
|---|---:|---:|---:|---:|---:|---:|
| Tue–Fri, all sessions | 669 | -52.15R | -0.078R | -0.109R | 59.90R | 0 |
| Mon–Fri, all sessions | 837 | -70.52R | -0.084R | -0.116R | 71.85R | 0 |
| Tue–Fri, no Asia | 527 | -37.63R | -0.071R | -0.100R | 55.17R | 0 |
| Mon–Fri, no Asia | 646 | -53.92R | -0.083R | -0.113R | 64.90R | 0 |

Adding Monday worsened the portfolio. Removing Asia reduced losses but did not create a positive or cost-robust strategy.

## Session decomposition

| Arm | Trades | Net R | Expectancy | +1 pip each side | Max DD | Positive years |
|---|---:|---:|---:|---:|---:|---:|
| London only | 284 | -24.66R | -0.087R | -0.117R | 31.89R | 1 |
| New York only | 266 | -19.96R | -0.075R | -0.101R | 31.24R | 1 |
| Asia only | 168 | -14.76R | -0.088R | -0.128R | 20.07R | 1 |
| London + New York | 527 | -37.63R | -0.071R | -0.100R | 55.17R | 0 |
| London + Asia | 424 | -39.36R | -0.093R | -0.127R | 41.54R | 1 |
| Asia + New York | 434 | -34.72R | -0.080R | -0.111R | 43.80R | 0 |

No session arm was positive. The independent verifier reproduced all metrics, paired effects, and selection decisions.

## Strategic conclusion

The current DTR reversal core does not transfer to GBPUSD. The result is negative before additional one- and two-pip cost stress, so execution refinement cannot rescue it. No neighboring parameter search, Pine conversion, sizing, or deployment is authorized on this sample.

The corrected raw bid/ask cache is retained privately and is not committed or redistributed.
