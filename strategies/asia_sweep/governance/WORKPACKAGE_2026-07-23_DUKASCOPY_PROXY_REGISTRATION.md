# Work Package AS-WP-20260723-02 — Dukascopy Proxy Registration

## Objective

Reacquire and register the previously used Dukascopy Nasdaq and S&P proxy datasets for the standalone Asia Sweep research program without representing either dataset as CME futures data.

## Instruments

- `NQ_PROXY_DUKASCOPY_USATECH`: Dukascopy `usatechidxusd`, USA 100 Technical Index CFD proxy.
- `ES_PROXY_DUKASCOPY_USA500`: Dukascopy `usa500idxusd`, USA 500 Index CFD proxy.

## Frozen acquisition contract

- downloader: `dukascopy-node` version `1.49.0`;
- timeframe: one minute;
- price side: bid;
- requested range: `2022-12-26` through `2025-12-12`;
- source timestamps: UTC;
- normalized session timestamps: `America/New_York`;
- include volumes in units;
- include flat bars;
- retain raw download logs;
- produce deterministic ZIP and GZIP files plus SHA-256 inventory;
- do not commit raw market data to Git.

The final observed first and last timestamps are determined from the downloaded files rather than inferred from command arguments.

## Scope

- controlled re-download through GitHub Actions;
- strict UTC parsing and New York conversion;
- duplicate and off-grid timestamp rejection;
- quote-resolution inspection;
- deterministic normalized archives;
- checksums and provenance inventory;
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

## Acceptance criteria

1. Both downloads complete from the same package version and requested date range.
2. Each normalized dataset has unique on-grid minute timestamps.
3. UTC and New York timestamps are retained explicitly.
4. SHA-256 checksums, row counts, observed date bounds and quote increments are recorded.
5. Raw files remain outside Git and are delivered as workflow artifacts.
6. Independent review confirms the proxy/futures distinction is preserved.
7. Original DTR CI and Asia Sweep CI remain green.
8. No strategy P&L is generated or inspected.

## Next gate

After registration, generate Asia Sweep event ledgers for both proxies, audit session completeness, select at least 50 events per proxy for manual review and freeze event semantics before execution simulation.
