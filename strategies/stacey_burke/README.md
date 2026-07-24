# Stacey Burke Multi-Asset FX Research

This namespace contains a separate research programme for mechanically testable Stacey Burke liquidity concepts. It does not alter DTR, Asian Sweep or Stoic results.

The first research object is a conditional previous-day external-liquidity sweep-and-reclaim event census across a fixed, factor-diverse FX basket. Strategy rules remain blocked until source qualification and the event-frequency/mechanism gate are complete.

## Frozen initial universe

- EURUSD, GBPUSD, USDCHF
- AUDUSD, NZDUSD, USDCAD
- USDJPY, EURJPY, GBPJPY
- EURGBP

All instruments use Dukascopy one-minute BID and ASK data. Source acquisition preserves inactive records and produces annual immutable hashes.
