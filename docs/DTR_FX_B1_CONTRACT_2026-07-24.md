# DTR-FX B1 executable contract

Date: 2026-07-24  
Work package: `DTR-FX-WP-20260724-23`

## Decision

Freeze the provenance-complete 55-trade branch implementation of `FX_B1_PREVDAY_LONDON_BOS_MID` as the sole executable B1 contract.

This choice is not based on its higher historical expectancy. It is based on four audit properties that the 144-trade clean-room mechanism replication does not retain:

1. executable source;
2. checksum-bound source data;
3. complete trade identities and paths;
4. byte-for-byte deterministic reproduction.

The clean-room result remains useful only as evidence that the previous-day/London/midpoint mechanism survived a materially different implementation. Its returns and trade count are not interchangeable with the frozen executable contract.

## Frozen regression evidence

- Source period: 2022-01-01 through 2025-12-31.
- B1 trade ledger: 55 trades.
- Net result: +9.6861980886R.
- Net expectancy: +0.1761126925R.
- Gross expectancy: +0.2549031030R.
- Profit factor: 1.4240428268.
- 1.5× cost expectancy: +0.1294962015R.
- Locked 2025 expectancy: -0.0385059247R.
- Date-block 95% interval: crosses zero.
- Frozen B1 ledger SHA-256: `c1a9b6788d3a0f697614ee4c9f4c5a47a6c0fdf0e84f6444db2b5cdd6ffecddd`.

A fresh local reconstruction from the original checksum-matching private cache reproduced the B1 trade ledger, six-arm summary, funnel, audit, and decision files byte-for-byte.

## Data-format correction

The historical downloader labeled the Dukascopy BI5 fields as `open, high, low, close`, while the actual BI5 order is `open, close, low, high`. The frozen v0.1 runner corrected this at load time. New acquisitions write canonical OHLC directly. Source qualification must establish valid OHLC before strategy execution; this format normalization is not a strategy change.

## Next gate

Acquire and qualify 2015–2021 BID/ASK M1 files without running B1. After annual hashes are frozen, execute the unchanged contract in a separate package.
