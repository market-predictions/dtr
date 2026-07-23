# Work Package AS-WP-20260723-02 — Dukascopy Proxy Registration

## Objective

Reacquire and register the previously used Dukascopy Nasdaq and S&P proxy datasets for the standalone Asia Sweep research program without representing either dataset as CME futures data.

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
- normalized session timestamps: `America/New_York`;
- corrected BI5 field mapping: seconds, open, close, low, high, volume;
- index-price divisor: `1000.0`;
- feed-volume scaling: multiply by `1,000,000`;
- yearly acquisition slices with four daily workers per job;
- eight retries with exponential backoff and jitter;
- no synthetic candles for 404 or empty days;
- exclude zero-volume rows during qualification;
- retain yearly audit records and raw checksums;
- produce deterministic normalized ZIP and GZIP files plus SHA-256 inventory;
- do not commit raw market data to Git.

The static transport supersedes the initial package-API attempt after three HTTP 429 failures and recovery of the earlier successful DTR downloader. The amendment was frozen before inspecting new proxy artifacts or Asia Sweep event results.

The final observed first and last timestamps are determined from downloaded files rather than inferred from command arguments.

## Scope

- controlled re-download through GitHub Actions;
- strict UTC parsing and New York conversion;
- duplicate and off-grid timestamp rejection;
- positive-volume active-candle qualification;
- OHLC invariant checks;
- quote-resolution inspection;
- deterministic normalized archives;
- checksums and provenance inventory;
- comparison with the recovered prior USA500 structural qualification;
- proxy-specific manifests after artifact inspection;
- event-ledger generation without P&L after data qualification;
- manual audit sampling preparation.

## Separation and labeling rules

1. Proxy results remain separate from NQ and ES futures results.
2. Proxy evidence cannot validate futures execution costs, fills, roll handling or tradability.
3. The proxy series may test the market-structure hypothesis and cross-index transferability.
4. Strategy parameters remain identical across both proxies except declared instrument metadata.
5. No P&L is authorized in this work package.
6. No DTR strategy signal logic or frozen DTR result is modified.
7. No 2026 proxy data are opened in this acquisition.

## Acceptance criteria

1. Both downloads complete from the same static-feed implementation and requested date range.
2. Each normalized active dataset has unique on-grid minute timestamps.
3. UTC and New York timestamps are retained explicitly.
4. SHA-256 checksums, downloaded and active row counts, observed date bounds, zero-volume exclusions and quote increments are recorded.
5. OHLC invariants pass.
6. Raw files remain outside Git and are delivered as workflow artifacts.
7. Independent review confirms the proxy/futures distinction is preserved.
8. Original DTR CI and Asia Sweep CI remain green.
9. No strategy P&L is generated or inspected.

## Next gate

After registration, generate Asia Sweep event ledgers for both proxies, audit session completeness, select at least 50 events per proxy for manual review and freeze event semantics before execution simulation.
