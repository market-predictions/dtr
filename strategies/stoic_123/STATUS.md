# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.2.0-research`
Work package: `STOIC123-WP-20260723-01`
Decision state: `GBPUSD_PHASE1_COMPLETE_NO_EDGE__INDEX_PROXY_OFFICIAL_RUN_PENDING`

## Complete

- Dedicated strategy namespace and governance tree.
- Frozen six-arm phase-one candidate family; configuration unchanged.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- Canonical proxy archives and manifests stored in the private Google Drive cache.
- Corrected active-minute GBPUSD bid/ask archive and manifest stored in Drive.
- Causal multi-timeframe detector with exact original-versus-optimized equivalence across all six arms.
- Side-correct GBPUSD execution and stop semantics.
- Four-year GBPUSD phase-one run with 10,000-iteration date-block inference.
- Independent trade-ledger reconstruction passing for all six GBPUSD arms.
- Fourteen dedicated tests passing locally.

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

## Pending

- Produce clean official, separate NQ-proxy and ES-proxy result packages after resolving the multi-source transition-performance bottleneck.
- Run the qualified NQ futures archive when mounted.
- Obtain repository CI confirmation for this version.

## Scientific restrictions

- No DTR baseline or DTR test result is changed.
- No pooled optimization.
- No proxy-specific or GBPUSD-specific tuning from inspected returns.
- No CME claim from index-CFD proxies.
- No broker-neutral FX claim from one provider stream.
- No live trading, sizing, or Pine authorization.
