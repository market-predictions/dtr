# Dukascopy Proxy Data Preregistration

## Status

`ACQUISITION_AUTHORIZED_RESULTS_NOT_INSPECTED`

## Purpose

Register two Dukascopy CFD index series as proxy datasets for testing the Asia Sweep market-structure hypothesis. These datasets do not replace or impersonate CME NQ or ES futures.

## Frozen proxy mapping

| Research ID | Dukascopy instrument | Description | Futures relationship |
|---|---|---|---|
| `NQ_PROXY_DUKASCOPY_USATECH` | `usatechidxusd` | USA 100 Technical Index CFD | Nasdaq/NQ directional proxy only |
| `ES_PROXY_DUKASCOPY_USA500` | `usa500idxusd` | USA 500 Index CFD | S&P/ES directional proxy only |

## Frozen acquisition parameters

- package: `dukascopy-node`;
- version: `1.49.0`;
- requested start: `2022-12-26`;
- requested end: `2025-12-12`;
- timeframe: `m1`;
- price type: bid;
- source timezone: UTC;
- session timezone: `America/New_York`;
- volume: included in units;
- flat bars: included;
- retries: five, including successful empty responses;
- output: normalized deterministic ZIP and GZIP archives;
- retention: GitHub Actions artifact only; no raw market data committed.

The actual observed first and last timestamps must be taken from the downloaded rows. The command-date boundary is not assumed to be inclusive or exclusive until inspected.

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
3. Register proxy-specific manifests.
4. Generate event ledgers without P&L.
5. Audit at least 50 events from each proxy.
6. Freeze any necessary semantic corrections before execution simulation.
7. Treat later P&L as proxy evidence only and require futures confirmation separately.
