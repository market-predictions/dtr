# Dukascopy Proxy Data Preregistration

## Status

`STATIC_TRANSPORT_AMENDMENT_FROZEN_BEFORE_NEW_ARTIFACT_INSPECTION`

## Purpose

Register two Dukascopy CFD index series as proxy datasets for testing the Asia Sweep market-structure hypothesis. These datasets do not replace or impersonate CME NQ or ES futures.

## Frozen proxy mapping

| Research ID | Dukascopy instrument | Description | Futures relationship |
|---|---|---|---|
| `NQ_PROXY_DUKASCOPY_USATECH` | `usatechidxusd` | USA 100 Technical Index CFD | Nasdaq/NQ directional proxy only |
| `ES_PROXY_DUKASCOPY_USA500` | `usa500idxusd` | USA 500 Index CFD | S&P/ES directional proxy only |

## Transport amendment

The initial reacquisition attempt used `dukascopy-node` v1.49.0 over a multi-year request and repeatedly received HTTP 429 before normalization. Repository history then recovered the prior successful DTR transport implementation and the earlier USA500 qualification record. Before inspecting any new artifact, the acquisition contract was amended to reproduce that proven static-feed method.

This is a transport correction based on prior provenance evidence. It does not use Asia Sweep event counts, signals or P&L.

## Frozen acquisition parameters

- provider endpoint: Dukascopy static daily BI5 candle feed;
- downloader: `scripts/download_dukascopy_static_proxy.py`;
- requested start: `2022-01-01`;
- requested end: `2026-01-01`, end-exclusive;
- yearly slices: 2022, 2023, 2024 and 2025;
- timeframe: one minute;
- price type: bid;
- source timezone: UTC;
- session timezone: `America/New_York`;
- BI5 record mapping: seconds, open, close, low, high, volume;
- price divisor: `1000.0` for both index proxies;
- feed-volume conversion: multiply raw float by `1,000,000`;
- maximum daily download workers: four per yearly job;
- retry policy: eight attempts with exponential backoff and jitter;
- HTTP 404 and empty days: retained in audit counts, with no synthetic candle creation;
- zero-volume rows: excluded during qualification;
- output: normalized deterministic ZIP and GZIP archives;
- retention: GitHub Actions artifact only; no raw market data committed.

The actual observed first and last timestamps must be taken from downloaded rows. The command boundary is not treated as proof of coverage.

## Recovered prior evidence

The earlier USA500 qualification reported 1,747,387 downloaded rows, 399,309 synthetic zero-volume placeholders removed, 1,348,078 active candles retained, zero duplicates and a 2022-01-02 through 2025-12-31 active range. Those facts are used only as a transport and qualification cross-check for the reacquisition; they are not Asia Sweep results.

## Permitted conclusions

The proxy datasets may be used to evaluate:

- Asia high/low construction;
- sweep and reclaim frequency;
- confirmation-state behavior;
- cross-index transferability;
- session and weekday concentration;
- event-ledger reproducibility;
- data-quality sensitivity.

## Prohibited conclusions

The proxy datasets may not establish:

- CME futures execution quality;
- futures tick-level fill realism;
- futures volume behavior;
- futures contract-roll robustness;
- futures commissions, slippage or liquidity;
- deployment readiness for NQ or ES.

## Frozen signal-threshold policy

The strategy continues to use the preregistered futures-equivalent `0.25` index-point signal tick for two-tick sweep and stop-buffer definitions. The proxy's observed quote increment is recorded separately and may not be substituted after inspecting results.

## Decision sequence

1. Download and checksum both proxies.
2. Inspect schema, timestamps, quote increments and market-hour gaps.
3. Compare the reacquired USA500 structural inventory with the prior qualification record.
4. Register proxy-specific manifests.
5. Generate event ledgers without P&L.
6. Audit at least 50 events from each proxy.
7. Freeze any necessary semantic corrections before execution simulation.
8. Treat later P&L as proxy evidence only and require futures confirmation separately.
