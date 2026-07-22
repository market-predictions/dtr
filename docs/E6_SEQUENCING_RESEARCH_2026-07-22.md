# E6 Portfolio Sequencing Research — 2026-07-22

## Decision

`RETAIN_S0_GLOBAL_SEQUENCING`

The current E6 portfolio rule—one open position at a time across Asia, London and New York—remains the best tested sequencing architecture. None of the frozen alternatives improved risk-adjusted portfolio performance.

No E6 signal, Pine, sizing or deployment change follows from this historical study.

## Provenance and regression

- Raw NQ archive SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Input E6 signal diagnostics SHA-256: `39b48d9e6219357907eac1bf65d81d2dff392d1d172916008ad20365665693ad`.
- Frozen E6 baseline reproduced exactly: 304 trades, 48.937550R, 0.160979R expectancy, 8.632571R maximum drawdown and 5.668942 return/DD.
- Costs remained one tick slippage on entry, one tick on exit and $2.25 commission per side.

## Frozen arms

- **S0:** current global one-open-position sequencing.
- **S1:** first executable E6 trade per ETH market date.
- **S2:** current global sequencing plus a 60-minute cooldown after every exit.
- **S3:** independent Asia, London and New York sleeves, with one-third normal risk per trade.

## Results

| Arm | Trades | Risk-normalized net R | Raw expectancy | Max DD | Return/DD | 2-tick/side expectancy | Decision |
|---|---:|---:|---:|---:|---:|---:|---|
| S0 current global | 304 | **48.94** | **0.161** | 8.63 | **5.67** | **0.143** | Retain |
| S1 first per ETH date | 259 | 41.73 | 0.161 | 8.76 | 4.77 | 0.143 | Reject |
| S2 60-minute cooldown | 300 | 47.73 | 0.159 | **8.63** | 5.53 | 0.141 | Reject |
| S3 session sleeves | 310 | 15.58 | 0.151 | 3.19 | 4.89 | 0.133 | Reject |

### S1 — first trade per ETH date

S1 removed 45 otherwise executed E6 trades. Those removed trades earned 7.20R. Per-trade expectancy was virtually unchanged, so the rule did not improve selection quality; it merely reduced opportunity and total return.

### S2 — 60-minute cooldown

S2 removed only four E6 trades. Those trades earned 1.20R. The equity path and drawdown were almost identical to S0, but return and return/DD were slightly lower. The cooldown adds operational delay without measurable benefit.

### S3 — independent session sleeves

S3 retained all 304 S0 trades and enabled six additional trades, but those six trades lost 2.19R. Only 12 trades participated in any cross-session overlap and the maximum concurrency was two positions. Because each sleeve permanently used one-third risk, most trades were materially under-sized while actual overlap was rare. Risk-normalized net return fell to 15.58R.

This does not prove that all multi-position portfolio designs are bad. It shows that the frozen equal one-third sleeve design is inefficient for this sparse overlap pattern and should not be optimized further on the current sample.

## Paired ETH-date inference

| Arm | Incremental net R vs S0 | 95% interval | Probability of improvement | Familywise p |
|---|---:|---:|---:|---:|
| S1 | -7.20R | [-24.66, +8.39] | 19.5% | 1.000 |
| S2 | -1.20R | [-8.01, +4.05] | 36.9% | 1.000 |
| S3 | -33.36R | [-62.41, -4.22] | 1.3% | 1.000 |

An independent reconstruction with a different seed reached the same conclusion. S3 remained clearly inferior; S1 and S2 had no evidence of positive incremental value.

## Strategic interpretation

E6 does not appear to suffer from excessive overtrading or harmful immediate re-entry. Its current global position constraint already removes most conflicts while preserving profitable later-session opportunities.

The overlap opportunity is too sparse to justify permanently dividing risk into three session budgets. The current single portfolio makes better use of available capital.

## Tactical decision

- retain S0 current global sequencing;
- reject first-trade-per-day restriction;
- reject 60-minute cooldown;
- reject fixed one-third session sleeves;
- do not search alternate cooldowns, daily limits, sleeve weights or dynamic reallocation on 2023–2025;
- keep E6 unchanged.

## Independent review and determinism

The reviewer reconstructed all four arms, metrics, cost stresses, daily and cooldown contracts, session-sleeve position constraints, risk cap, changed-trade attribution and independent bootstrap inference. All checks passed.

Two complete executions produced byte-identical output artifacts.

## Next authorized work

Proceed to Block 5: official FOMC, CPI, Employment Situation/NFP, quarterly-expiration, early-close and detected rollover-window attribution. This block is diagnostic only and cannot create an exclusion filter from the current historical sample.
