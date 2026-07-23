# GBPUSD DTR Replication — 2026-07-23

## Decision

`NO_VIABLE_GBPUSD_DTR_BASELINE`

This study applies the frozen Day Trader Rauf core to temporary Dukascopy GBPUSD one-minute bid/ask data from 2022 through 2025. Signals use synchronized midpoint OHLC; the base execution model uses the observed 75th-percentile spread plus 0.1 pip slippage and a $3.50 commission per side for one standard lot.

## Data and execution audit

- Synchronized active candles: 1,488,142
- Active period: 2022-01-02 17:01:00 through 2025-12-31 16:58:00
- Median quoted spread: 0.900 pips
- 75th-percentile spread: 1.100 pips
- Base modeled slippage: 0.650 pips per side
- Eligible covered sessions: 3,056

## Monday × Asia factorial

| arm                |   trades |    net_r |   expectancy_r |   one_pip_each_side_expectancy_r |   max_drawdown_r |   positive_years | gate_all   |
|:-------------------|---------:|---------:|---------------:|---------------------------------:|-----------------:|-----------------:|:-----------|
| P0_TUE_FRI_ALL     |      669 | -52.1457 |        -0.0779 |                          -0.1093 |          59.9042 |                0 | False      |
| P1_MON_FRI_ALL     |      837 | -70.5200 |        -0.0843 |                          -0.1161 |          71.8531 |                0 | False      |
| P2_TUE_FRI_NO_ASIA |      527 | -37.6297 |        -0.0714 |                          -0.0998 |          55.1725 |                0 | False      |
| P3_MON_FRI_NO_ASIA |      646 | -53.9245 |        -0.0835 |                          -0.1127 |          64.8976 |                0 | False      |

## Session decomposition

| arm                |   trades |    net_r |   expectancy_r |   one_pip_each_side_expectancy_r |   max_drawdown_r |   positive_years | gate_all   |
|:-------------------|---------:|---------:|---------------:|---------------------------------:|-----------------:|-----------------:|:-----------|
| S1_LONDON_ONLY     |      284 | -24.6599 |        -0.0868 |                          -0.1173 |          31.8948 |                1 | False      |
| S2_NEW_YORK_ONLY   |      266 | -19.9618 |        -0.0750 |                          -0.1010 |          31.2423 |                1 | False      |
| S3_ASIA_ONLY       |      168 | -14.7558 |        -0.0878 |                          -0.1281 |          20.0729 |                1 | False      |
| S4_LONDON_NEW_YORK |      527 | -37.6297 |        -0.0714 |                          -0.0998 |          55.1725 |                0 | False      |
| S5_LONDON_ASIA     |      424 | -39.3611 |        -0.0928 |                          -0.1272 |          41.5387 |                1 | False      |
| S6_ASIA_NEW_YORK   |      434 | -34.7176 |        -0.0800 |                          -0.1115 |          43.8043 |                0 | False      |

## Interpretation

Neither the frozen broad arms nor the bounded session decomposition produced a cost-robust and year-stable GBPUSD baseline. No neighboring parameter search is authorized on this sample.

This is exploratory cross-asset evidence. It does not authorize Pine conversion, position sizing, or live deployment.
