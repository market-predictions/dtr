# DTR-ESPROXY-WP-20260722-17 — Dukascopy USA500 proxy acquisition and qualification

## Objective

Acquire and qualify a temporary multi-year one-minute S&P 500 proxy dataset for unchanged DTR cross-market replication.

## Source contract

- Downloader: `Leo4815162342/dukascopy-node` v1.49.0.
- Instrument: `usa500idxusd` / `USA500.IDX/USD`.
- Price type: bid.
- Timeframe: one minute.
- Range: 2022-01-01 through 2026-01-01, end-exclusive.
- Raw market data must not be committed to GitHub, published, or redistributed.
- Temporary GitHub Actions artifacts expire after one day; local data must be deleted after research use.

## Qualification gates

- source and downloader version recorded;
- annual artifacts and uncompressed CSV hashes verified;
- timestamps sorted and unique;
- OHLC integrity verified;
- synthetic flat zero-volume placeholders removed;
- London, New York and overnight session coverage audited;
- discontinuities and known proxy limitations documented.

## Decision boundary

This is S&P 500 CFD proxy data, not CME ES futures. Any subsequent result must be labelled proxy replication and cannot validate CME execution, volume, spread, roll or contract behavior.

## Outcome

`QUALIFIED_WITH_PROXY_LIMITATIONS`

The cleaned dataset contains 1,348,078 active one-minute bid candles from 2022-01-02 23:00 UTC through 2025-12-31 21:13 UTC. Original E6 and E6 no-FOMC may now be tested unchanged, side by side, with explicit conservative costs and no proxy-specific retuning.
