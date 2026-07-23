# Phase-One Proxy Results — Stoic Edge 1-2-3

Date: 2026-07-23
Status: `PASS_EXECUTION__POSITIVE_BUT_UNCERTAIN`
Configuration SHA-256: `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`

## Source qualification

### NQ proxy

- Source: Dukascopy USATECH bid-CFD full-grid M1 archive.
- SHA-256: `b98f08a0fd35255c09232d41da10ee84559587067b48e942cccdbe37b0b888c4`.
- Full-grid rows: 2,103,840.
- Active rows: 1,366,578.
- Duplicate timestamps: zero.
- Classification: Nasdaq-100 proxy with NQ-equivalent research economics; not CME NQ futures.

### ES proxy

- Source: Dukascopy USA500 bid-CFD full-grid M1 archive.
- SHA-256: `a2342f9d64695d8ecb618a907600b4de0b1433ba65d25c1f0ac3d0566ab9a72f`.
- Full-grid rows: 2,103,840.
- Active rows: 1,348,073.
- Duplicate timestamps: zero.
- Classification: S&P-500 proxy with ES-equivalent research economics; not CME ES futures.

## NQ-proxy results

| Arm | Trades | Net R | Expectancy R | Profit factor | 95% bootstrap interval |
|---|---:|---:|---:|---:|---:|
| No-map control | 1,141 | 179.20 | 0.157 | 1.174 | [-0.109, 0.460] |
| EMA map | 472 | 86.07 | 0.182 | 1.200 | [-0.186, 0.585] |
| Breakout map | 305 | 42.91 | 0.141 | 1.163 | [-0.274, 0.612] |
| EMA + breakout | 260 | 45.12 | 0.174 | 1.199 | [-0.277, 0.710] |
| Strict base | 155 | -18.96 | -0.122 | 0.871 | [-0.660, 0.548] |
| Strict close | 438 | 89.33 | 0.204 | 1.224 | [-0.177, 0.630] |

All positive arms lose money in 2023. The result therefore contains meaningful chronological instability despite positive total expectancy.

## ES-proxy results

| Arm | Trades | Net R | Expectancy R | Profit factor | 95% bootstrap interval |
|---|---:|---:|---:|---:|---:|
| No-map control | 1,068 | 67.23 | 0.063 | 1.067 | [-0.160, 0.301] |
| EMA map | 456 | 2.37 | 0.005 | 1.005 | [-0.329, 0.372] |
| Breakout map | 313 | 8.63 | 0.028 | 1.030 | [-0.359, 0.457] |
| EMA + breakout | 265 | 30.46 | 0.115 | 1.123 | [-0.323, 0.623] |
| Strict base | 156 | -5.08 | -0.033 | 0.968 | [-0.612, 0.646] |
| Strict close | 420 | 43.65 | 0.104 | 1.110 | [-0.258, 0.502] |

Performance is weaker than NQ proxy. The strict-close arm is positive on both proxies, but ES proxy remains negative in 2023 and 2024 for that arm.

## Independent review

For all twelve instrument-arm ledgers:

- trade count reconstruction matched;
- net R reconstruction matched;
- expectancy reconstruction matched;
- overlapping positions: zero;
- invalid initial risks: zero;
- chronology violations: zero.

## Decision

`ROBUSTNESS_TESTING_AUTHORIZED__NO_PROMOTION`

The broad cross-proxy positivity is sufficient to justify preregistered robustness work. It is insufficient for promotion because every 95% interval crosses zero, NQ proxy has a common 2023 failure, and ES proxy is materially weaker. Strict close is the primary cross-proxy candidate; no-map control remains the essential simplicity benchmark.
