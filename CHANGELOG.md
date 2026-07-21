# Changelog

## v0.1.0 — 2026-07-21

### Added

- Initial DTR Optimization Lab repository structure.
- Python packaging and dependency configuration.
- Data-safe `.gitignore` that excludes raw market data and generated artifacts.
- NQ one-minute dataset catalog with checksum, schema, date range, and audit findings.
- CSV/ZIP loader with strict schema validation.
- OHLCV resampling utility for one-minute to five-minute research bars.
- Deterministic dataset audit model and command-line interface.
- Unit tests for audit and resampling semantics.
- GitHub Actions CI for Python 3.11 and 3.12.

### Why

The DTR Pine strategy requires systematic parity testing, funnel diagnostics, and controlled optimization outside TradingView. The first release establishes reproducible data handling before any strategy optimization begins.

### Known limitations

- Contract rollover and back-adjustment semantics are not yet resolved.
- Source timestamps are still timezone-naive pending bar-open/bar-close verification.
- The uploaded dataset appears capped at the Excel worksheet row limit and ends mid-session.
- No DTR strategy logic has been ported yet.

### Next

- Complete the NQ dataset integrity and contract-continuity audit.
- Define TradingView parity fixtures.
- Implement session-range and sweep primitives.
- Build the baseline setup funnel before testing parameter alternatives.
