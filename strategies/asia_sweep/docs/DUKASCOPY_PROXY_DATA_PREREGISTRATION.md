# Dukascopy Proxy Data Preregistration

## Status

`FULL_GRID_ACTIVITY_AMENDMENT_FROZEN_BEFORE_EVENT_RECOMPUTATION`

## Purpose

Register two Dukascopy CFD index series as proxy datasets for testing the Asia Sweep market-structure hypothesis. These datasets do not replace or impersonate CME NQ or ES futures.

## Frozen proxy mapping

| Research ID | Dukascopy instrument | Description | Futures relationship |
|---|---|---|---|
| `NQ_PROXY_DUKASCOPY_USATECH` | `usatechidxusd` | USA 100 Technical Index CFD | Nasdaq/NQ directional proxy only |
| `ES_PROXY_DUKASCOPY_USA500` | `usa500idxusd` | USA 500 Index CFD | S&P/ES directional proxy only |

## Transport amendments

The initial reacquisition attempt used `dukascopy-node` v1.49.0 over a multi-year request and repeatedly received HTTP 429 before normalization. Repository history then recovered the prior successful DTR static-BI5 transport. That transport correction was frozen before inspecting new artifacts.

The first successful qualification retained only positive-volume candles. Structural inspection then showed that Dukascopy supplies a complete one-minute quote grid containing zero-volume carry-forward rows. Removing those rows falsely converts normal inactive minutes into missing-data defects. Retaining them without an activity gate can make closed or stale periods appear tradable.

Before recomputing any official event ledger, and without inspecting strategy P&L, the canonical data contract was therefore amended to retain the complete source quote grid and audit activity separately. This is a data-semantics correction, not a result-driven strategy change.

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
- HTTP 404 and empty days: retained in yearly audit counts; the downloader creates no replacement candles;
- source zero-volume rows: retained as carry-forward quote observations;
- UTC timestamp: authoritative and unique;
- New York timestamp: retained with explicit UTC offset to preserve DST disambiguation;
- output: deterministic full-grid ZIP and GZIP archives;
- retention: GitHub Actions artifact only; no raw market data committed.

The actual observed first and last timestamps and every checksum are taken from acquired rows rather than inferred from command arguments.

## Frozen activity and staleness gate

The following rule is applied independently to the Asia range, execution window and pre-signal path:

1. The complete expected one-minute half-open interval must exist.
2. At least one minute must have positive source volume.
3. No consecutive run of zero-volume source rows may exceed 10 minutes.

The 10-minute limit was chosen from signal-timeframe geometry, not returns: a longer stale run would create more than two consecutive synthetic five-minute signal bars. A fixed percentage-volume threshold is rejected because legitimate overnight activity differs materially between the USATECH and USA500 proxies.

## Source-revision disclosure

A prior USATECH artifact and the reacquired source differ at exactly one minute: `2024-10-09T23:05:00Z`. The prior snapshot reported an active candle; the current Dukascopy feed reports a zero-volume carry-forward quote. The reacquired snapshot and its checksums are canonical. The one-row upstream revision must remain documented in qualification reports and cannot be silently reconciled.

## Recovered prior evidence

The earlier USA500 qualification reported an active-candle dataset with zero duplicates and a 2022-01-02 through 2025-12-31 active range. That record remains only a transport and structural cross-check. The canonical Asia Sweep dataset is the newly acquired full quote grid.

## Permitted conclusions

The proxy datasets may be used to evaluate:

- Asia high/low construction;
- sweep and reclaim frequency;
- confirmation-state behavior;
- cross-index transferability;
- session and weekday concentration;
- event-ledger reproducibility;
- data-quality and source-revision sensitivity.

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

1. Produce and checksum the canonical full-grid proxy archives.
2. Verify duplicate, grid, OHLC, timezone and activity metadata.
3. Register proxy-specific manifests using UTC source timestamps and New York session semantics.
4. Implement the frozen activity gate before official event generation.
5. Correct the end-of-window entry defect in a separate event-semantics work package.
6. Generate event ledgers without P&L.
7. Audit at least 50 events from each proxy.
8. Freeze any remaining semantic corrections before execution simulation.
9. Treat later P&L as proxy evidence only and require futures confirmation separately.
