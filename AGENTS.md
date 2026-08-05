# AGENTS.md

## CACHE-FIRST CONTROL — MANDATORY

Before starting **any** strategy test, market-data audit, FX research programme, cross-pair study, or Dukascopy acquisition in this repository:

1. Read `REPOSITORY_CONTROL.md`.
2. Read `docs/PERMANENT_MARKET_DATA_CACHE.md`.
3. Read `data/private_market_data_cache_registry.json`.
4. Search the canonical private Google Drive cache first.
5. Verify the registered SHA-256 values and reuse the qualified cached data.

Canonical dataset folder:

- `FX_M1_BID_ASK_2015_2025_PLUS_2026YTD`
- Drive folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`
- Ten pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP
- Coverage: complete 2015–2025 plus 2026 YTD ending exclusive 2026-07-24
- Format: Dukascopy M1, separate BID and ASK, UTC, qualified and checksummed

**Never reacquire full historic data that is already registered.**

A download is allowed only for a proven missing/corrupt partition, a materially different data construction, or an explicitly requested incremental extension. Record the exception in the work package, changelog, and registry before acquisition. Upload and verify the permanent copy before deleting temporary files.

Raw market data must never be committed to the public repository.

## Research operating rules

- Treat `REPOSITORY_CONTROL.md` as the repository-wide authority.
- Treat strategy-specific status files as subordinate to repository-wide data controls.
- Preserve holdout boundaries and preregistration.
- Separate discovery, validation, holdout and monitoring periods.
- Preserve negative results and do not rescue failed hypotheses through retrospective variants.
- Verify dataset checksums before performance execution.
- Do not generalize a pair-specific result without cross-pair evidence.
- Do not release Pine, alerts, sizing or deployment guidance before the relevant scientific and operational gates pass.
