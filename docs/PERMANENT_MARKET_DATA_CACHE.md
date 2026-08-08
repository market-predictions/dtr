# Permanent Private Market Data Cache

## CACHE-FIRST CONTROL — MANDATORY

Before any strategy test, event study, cross-pair replication, data audit, or Dukascopy acquisition, read `AGENTS.md`, `REPOSITORY_CONTROL.md`, and `data/private_market_data_cache_registry.json`. Search and verify the cache first. Full historic reacquisition of registered data is prohibited.

## Canonical permanent location

- Private Google Drive dataset folder: `FX_M1_BID_ASK_2015_2025_PLUS_2026YTD`
- Dataset folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`
- Source archives folder ID: `1X0Kajgx9yQ9-RAvRVDV5WDCaxVMXo858`
- Qualification folder ID: `1E1lLqClQrhVWIox_1Q1ddLl0jxNPcXxE`
- Privacy verified 2026-08-06: private, not shared, owner-only.

The public repository stores identifiers, checksums, schema, provenance and restore instructions only. It does not store raw candles.

## Dataset contract

- Canonical research name: **Dukascopy FX Cash**.
- Research dataset ID: `dukascopy_fx_cash_m1_bid_ask_v1`.
- Legacy technical catalog key remains unchanged for backward compatibility.
- Pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP.
- Dukascopy M1, separate BID and ASK, UTC.
- Complete 2015–2025 plus 2026 YTD ending exclusive 2026-07-24.
- Annual compressed CSV files, annual audits and pair source manifests.

Every study using this ten-pair source must also follow `research_registry/DUKASCOPY_FX_CASH_RESEARCH_STANDARD.md` and register its methodology/outcome under `research_registry/dukascopy_fx_cash/`. The market-data cache registry proves source identity; the research registry preserves scientific memory. They are complementary and neither replaces the other.

The original source ZIPs were split without transformation into 64 MiB binary parts because the Drive connector has a 100 MB transfer limit. Concatenating parts in registered order reconstructs the exact source artifact. The registry contains every pair-folder ID, part size, part SHA-256, original ZIP size and original ZIP SHA-256.

## Restore procedure

```bash
python scripts/restore_private_market_data_cache.py \
  --registry data/private_market_data_cache_registry.json \
  --pair EURUSD \
  --parts-dir /path/to/downloaded/EURUSD \
  --output /path/to/cache/EURUSD_DUKASCOPY_M1_BID_ASK_2015_2025_2026YTD.zip \
  --extract-to /path/to/cache/EURUSD
```

The utility verifies all part hashes, reconstructs the ZIP, verifies the original archive hash, checks extraction paths and extracts only after verification.

## Acquisition exception

A download may occur only for a proven missing or corrupt partition, an explicitly requested incremental period after 2026-07-24, or a materially different source construction. Before acquisition, record `CACHE_MISS_AUTHORIZATION:` and explain why the permanent cache is insufficient in the work package and changelog. Add and verify the new permanent copy before deleting temporary data.

## Verification evidence

A real EURUSD restore drill reconstructed the exact 130,281,961-byte source ZIP, matched SHA-256 `ce7a82e08c1088e003917b1cd4908f194c9fa8245d30ef61fa5401f7571a042d`, and extracted all annual BID/ASK files, audits and the source manifest safely.

## Durability

Google Drive is the canonical durable copy. GitHub Actions artifacts are temporary recovery evidence only. A second encrypted off-provider mirror is an open resilience-hardening item and does not authorize reacquisition while the canonical cache is healthy.
