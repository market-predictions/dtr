# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.2.0-research`
Work package: `STOIC123-WP-20260723-01`
Decision state: `PHASE1_COMPLETE__GBPUSD_NO_EDGE__INDEX_PROXIES_POSITIVE_UNCERTAIN`

## Complete

- Dedicated strategy namespace and governance tree.
- Frozen six-arm phase-one candidate family; configuration unchanged.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- Canonical proxy archives and manifests stored in the private Google Drive cache.
- Corrected active-minute GBPUSD bid/ask archive and manifest stored in Drive.
- Causal multi-timeframe detector with exact original-versus-optimized equivalence across all six arms.
- Side-correct GBPUSD execution and stop semantics.
- Separate four-year GBPUSD, NQ-proxy, and ES-proxy phase-one runs with 10,000-iteration date-block inference.
- Independent trade-ledger reconstruction passing for every arm and instrument.
- Fourteen dedicated tests passing in repository CI.
- Ruff and the complete repository suite passing on Python 3.11 and Python 3.12.

## GBPUSD decision

`REJECT_TRANSFER_NO_EDGE`

| Arm | Trades | Net R | Expectancy R | 95% bootstrap interval |
|---|---:|---:|---:|---:|
| No-map control | 1,233 | -555.69 | -0.451 | [-0.614, -0.262] |
| EMA map | 512 | -308.62 | -0.603 | [-0.828, -0.328] |
| Breakout map | 321 | -206.86 | -0.644 | [-0.840, -0.423] |
| EMA + breakout | 269 | -211.85 | -0.788 | [-0.962, -0.581] |
| Strict base | 163 | -97.23 | -0.596 | [-0.971, 0.015] |
| Strict close | 473 | -267.76 | -0.566 | [-0.784, -0.316] |

The failure is broad, not a marginal cost issue. No GBPUSD parameter tuning is authorized.

## Index-proxy decision

`POSITIVE_BUT_UNCERTAIN__ROBUSTNESS_TESTING_AUTHORIZED`

| Instrument | Arm | Trades | Net R | Expectancy R | 95% bootstrap interval |
|---|---|---:|---:|---:|---:|
| NQ proxy | No-map control | 1,141 | 179.20 | 0.157 | [-0.109, 0.460] |
| NQ proxy | Strict close | 438 | 89.33 | 0.204 | [-0.177, 0.630] |
| ES proxy | No-map control | 1,068 | 67.23 | 0.063 | [-0.160, 0.301] |
| ES proxy | EMA + breakout | 265 | 30.46 | 0.115 | [-0.323, 0.623] |
| ES proxy | Strict close | 420 | 43.65 | 0.104 | [-0.258, 0.502] |

Five of six arms are positive on each proxy, but every date-block interval crosses zero. The strict-close arm is positive on both proxies and is the strongest cross-market robustness candidate. No arm is promoted as a validated strategy.

## Pending

- Run predeclared nearby-definition, timeframe, cost, and chronological robustness tests on the cross-proxy candidates.
- Compare proxy results against the qualified NQ futures archive when mounted.
- Determine whether the strict-close arm adds mechanism value beyond simpler EMA-break controls.

## Scientific restrictions

- No DTR baseline or DTR test result is changed.
- No pooled optimization.
- No proxy-specific or GBPUSD-specific tuning from inspected returns.
- No CME claim from index-CFD proxies.
- No broker-neutral FX claim from one provider stream.
- No live trading, sizing, or Pine authorization.
