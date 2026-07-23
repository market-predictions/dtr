# Work Package AS-WP-20260723-02 — Dukascopy Proxy Registration

## Objective

Reacquire and register Dukascopy Nasdaq and S&P index proxies for the standalone Asia Sweep research program without representing either dataset as CME futures data.

## Instruments

- `NQ_PROXY_DUKASCOPY_USATECH`: Dukascopy `usatechidxusd`, USA 100 Technical Index CFD proxy.
- `ES_PROXY_DUKASCOPY_USA500`: Dukascopy `usa500idxusd`, USA 500 Index CFD proxy.

## Frozen acquisition contract

- transport: Dukascopy static daily `BID_candles_min_1.bi5` files;
- implementation: `scripts/download_dukascopy_static_proxy.py`;
- timeframe: one minute;
- price side: bid;
- requested range: `2022-01-01` through `2026-01-01`, end-exclusive;
- source timestamps: UTC;
- session timestamps: `America/New_York` with explicit UTC offset;
- corrected BI5 field mapping: seconds, open, close, low, high, volume;
- index-price divisor: `1000.0`;
- feed-volume scaling: multiply by `1,000,000`;
- yearly acquisition slices with four daily workers per job;
- eight retries with exponential backoff and jitter;
- no downloader-created replacement candles for 404 or empty days;
- retain source-provided zero-volume carry-forward rows;
- retain yearly audit records and raw checksums;
- produce deterministic full-grid ZIP and GZIP files plus SHA-256 inventory;
- do not commit market data to Git.

The static transport superseded the initial package-API attempt after repeated HTTP 429 responses. A later structural audit superseded the positive-volume-only normalization because it misclassified source carry-forward rows as missing data. Both amendments were made before official event recomputation and without strategy P&L.

## Frozen activity gate

For each Asia range, execution window and pre-signal path:

- require the complete one-minute half-open interval;
- require at least one positive-volume minute;
- reject a consecutive zero-volume run longer than 10 minutes.

The threshold is tied to the five-minute signal clock: more than 10 stale minutes would create more than two consecutive synthetic signal bars.

## Scope

- controlled reacquisition through GitHub Actions;
- strict UTC parsing and offset-aware New York conversion;
- duplicate, off-grid and non-one-minute-gap rejection;
- full quote-grid retention;
- positive/zero-volume inventory;
- OHLC invariant checks;
- quote-resolution inspection;
- deterministic normalized archives;
- checksums and provenance inventory;
- source-revision disclosure;
- proxy-specific manifests after artifact inspection;
- event-ledger preparation without P&L;
- manual audit sampling preparation.

## Separation and labeling rules

1. Proxy results remain separate from NQ and ES futures results.
2. Proxy evidence cannot validate futures execution costs, fills, roll handling or tradability.
3. The proxy series may test market-structure logic and cross-index transferability.
4. Strategy parameters remain identical across both proxies except declared instrument metadata.
5. No P&L is authorized in this work package.
6. No active DTR signal logic or frozen DTR result is modified.
7. No 2026 proxy rows are acquired or inspected.
8. Upstream source revisions are disclosed rather than silently reconciled.

## Acceptance criteria

1. All eight yearly downloads complete from the same static-feed implementation.
2. Each proxy retains exactly 2,103,840 one-minute source rows covering 2022–2025.
3. UTC timestamps are unique, on-grid and adjacent at exactly one-minute intervals.
4. New York timestamps retain explicit UTC offsets.
5. SHA-256 checksums, full-grid counts, positive/zero-volume counts, observed date bounds and quote increments are recorded.
6. OHLC invariants pass on all retained rows.
7. The frozen activity gate is documented and selected without P&L.
8. The one-row USATECH source revision at `2024-10-09T23:05:00Z` is disclosed.
9. Raw files remain outside Git and are delivered as workflow artifacts.
10. Independent review confirms the proxy/futures distinction and causal data handling.
11. Original DTR CI and isolated Asia Sweep CI are green.
12. No strategy P&L is generated or inspected.

## Next gate

After registration, implement proxy timezone/activity handling and the end-of-window entry correction in a separate event-semantics work package. Then generate official no-P&L ledgers and audit at least 50 events per proxy before execution simulation is authorized.
