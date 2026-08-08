# Dukascopy FX Cash — Dataset Contract

## Canonical identity

- Human name: **Dukascopy FX Cash**
- Research dataset ID: `dukascopy_fx_cash_m1_bid_ask_v1`
- Legacy catalog key: `dukascopy_fx_m1_bid_ask_2015_2025_2026_ytd`
- Provider: Dukascopy
- Market semantics: OTC cash/spot FX quote data
- Base timeframe: M1
- Quote sides: BID and ASK
- Source timezone: UTC
- Raw data in Git: prohibited

## Registered pair universe

EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP.

## Durable availability

- complete years: 2015–2025;
- 2026 YTD end exclusive: 2026-07-24;
- canonical private cache folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`;
- hashes/provenance registry: `data/private_market_data_cache_registry.json`;
- restore/acquisition runbook: `docs/PERMANENT_MARKET_DATA_CACHE.md`.

## Price semantics

Research must explicitly declare its price basis. Structural studies may use a midpoint only when justified and recorded. Executable strategy studies must model long/short entry and exit against the appropriate ASK/BID side plus declared slippage/cost assumptions.

JPY pip size is 0.01. Non-JPY pip size is 0.0001 unless the study documents an explicit normalization layer.

## Time semantics

The raw source is UTC. Any New York, London, Amsterdam, session, daily-close or DST-aware transformation must be defined in the study manifest. Calendar assumptions are model assumptions and cannot remain implicit.

## Data integrity

The permanent-cache contract remains authoritative. Do not download historic data merely because a research branch cannot see a prior workflow artifact. Restore and checksum-verify the registered cache first.

This contract does not establish that Dukascopy quotes are a consolidated global FX market or interdealer order book.
