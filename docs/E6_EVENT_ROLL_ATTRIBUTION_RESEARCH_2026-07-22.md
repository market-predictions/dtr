# E6 Event, Holiday and Rollover Attribution — 2026-07-22

## Decision

`RETAIN_E6_NO_EVENT_EXCLUSION_WATCH_FOMC_PRE_AND_ROLL_EXPIRY_OVERLAP`

E6 remains unchanged. The historical sample shows a credible risk warning around FOMC days, concentrated in trades entered before the 14:00 ET statement. Expiration-week and roll-window weakness is also visible, but both labels point mainly to the same 18-trade overlap cohort rather than two independent effects.

No event, holiday, expiration or rollover exclusion is authorized from the 2023–2025 sample.

## Provenance

- Registered NQ archive SHA-256 reproduced exactly: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Frozen E6 reproduced exactly: 304 trades, 48.937550R net, 0.160979R expectancy, 8.632571R maximum drawdown and 5.668942 return/DD.
- Normal costs remained one tick slippage per side and $2.25 commission per side.
- E6 signals, Tuesday–Friday calendar, sessions and global one-position sequencing were unchanged.

## Official date sources

- Federal Reserve FOMC calendars and statement dates: https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm
- BLS CPI release archive: https://www.bls.gov/bls/news-release/cpi.htm
- BLS Employment Situation archive: https://www.bls.gov/bls/news-release/empsit.htm
- CME equity-index roll convention and roll dates: https://www.cmegroup.com/trading/equity-index/rolldates.html
- CME holiday and special trading hours: https://www.cmegroup.com/trading-hours.html

Actual release dates were used, including delayed 2025 BLS releases.

## Main results

| Category | Trades | Net R | Expectancy | Classification |
|---|---:|---:|---:|---|
| FOMC day | 14 | -5.56R | -0.397R | WATCH_RISK |
| CPI day | 18 | +1.76R | +0.098R | NO_CLEAR_PATTERN |
| NFP day | 9 | +1.37R | +0.152R | DESCRIPTIVE_ONLY |
| Expiration week | 27 | -2.09R | -0.077R | WATCH_RISK |
| Roll window | 25 | -0.58R | -0.023R | WATCH_RISK |
| Expiration day | 3 | +0.59R | +0.195R | DESCRIPTIVE_ONLY |
| Early close | 1 | -1.03R | -1.025R | DESCRIPTIVE_ONLY |
| Shortened holiday | 1 | -1.03R | -1.028R | DESCRIPTIVE_ONLY |

### FOMC timing

The FOMC-day loss was concentrated before the statement:

- before 14:00 ET: 9 trades, -7.62R, -0.847R expectancy;
- after 14:00 ET: 5 trades, +2.06R, +0.412R expectancy;
- positions crossing the statement: 2 trades, -0.40R.

The independent date-block reconstruction again found the pre-statement cohort negative. However, nine trades remain below the frozen minimum for anything beyond descriptive risk monitoring. It is not sufficient to exclude FOMC days or pre-FOMC trades.

The pre-statement trades were five London and four New York trades. The weakness was therefore not produced by Asia trades after the announcement.

### Expiration and roll overlap

Expiration-week and roll-window labels overlap heavily:

| Cohort | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| Expiration week only | 9 | +3.11R | +0.346R |
| Roll window only | 7 | +4.62R | +0.660R |
| Both expiration and roll window | 18 | -5.20R | -0.289R |
| Neither | 270 | +46.40R | +0.172R |

The apparent weakness in both headline categories comes from the same shared transition cohort. The current evidence therefore does not support separate expiration-week and roll-window exclusions. The overlap should be monitored on longer or fresh data as one predefined risk cohort.

There were no E6 trades on the customary roll date itself because the frozen E6 calendar excludes Monday.

### Roll discontinuities

No official roll window contained a maintenance gap above the frozen global 99th-percentile threshold. Two windows nevertheless contained unusually large gaps:

- December 2024: 90.5 NQ points, approximately the 97.3rd percentile;
- June 2025: 94.0 NQ points, approximately the 97.6th percentile.

These remain data-quality warnings rather than strategy filters. Continuous-contract construction and adjustment methodology are still unresolved deployment gates.

### CPI, NFP and holidays

CPI-day performance was positive but modest and showed no clear adverse pattern. NFP also showed no clear problem, but only nine E6 trades occurred on NFP dates. Pre/post-release splits were too small for decisions.

Early-close and shortened-holiday evidence consisted of one trade each and is not interpretable.

## Independent review and determinism

The independent reviewer:

- reproduced the exact E6 baseline;
- rebuilt every category from the frozen official calendar;
- verified all release-time, expiration-week and roll-window masks;
- reconstructed all metrics and classifications;
- independently reconstructed the roll-gap diagnostics;
- reran date-block uncertainty with a different seed;
- confirmed the expiration/roll overlap decomposition.

All checks passed. Two complete primary executions and two independent reviews produced identical comparable artifacts.

## Strategic conclusion

The event study does not justify changing E6. It does identify two risks worth carrying forward unchanged:

1. FOMC-day trades, especially entries before the statement;
2. the fixed intersection of expiration week and the customary roll window.

Both require longer or fresh data before any decision. CPI, NFP, early-close and holiday exclusions have no supporting evidence.

## Next authorized work

Proceed to Block 6: fixed-fraction equity and execution-cost stress for unchanged E6. The stress block will quantify account growth, drawdown, time under water and tail risk at 0.50%, 1.00% and 1.50% current-equity risk under normal, two-tick-per-side and four-tick-per-side execution assumptions.

No Pine, sizing or deployment authorization follows from this historical attribution study.
