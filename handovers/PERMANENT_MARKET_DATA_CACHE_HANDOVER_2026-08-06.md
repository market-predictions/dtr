# Handover — Permanent Private Market Data Cache

## Current state

`PERMANENT_PRIVATE_FX_CACHE_ACTIVE_AND_VERIFIED`

Canonical Drive dataset folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`.

## First action for every future FX study

1. Read `AGENTS.md`.
2. Read `REPOSITORY_CONTROL.md`.
3. Read `data/private_market_data_cache_registry.json`.
4. Locate the pair folder in Drive.
5. Download all registered parts.
6. Run `scripts/restore_private_market_data_cache.py`.
7. Proceed only after all checksums pass.

## Prohibited shortcut

Do not start a new historical Dukascopy acquisition merely because raw files are absent from the public Git checkout or current Actions cache. Raw data is intentionally private and external to Git.

## Acquisition exception

Only a proven missing/corrupt partition, requested incremental extension, or materially different construction qualifies. Record `CACHE_MISS_AUTHORIZATION:` before acquisition.

## Validation

EURUSD was restored from its parts, matched the registered original archive SHA-256 and extracted safely.

## Open hardening item

Add a second encrypted off-provider mirror and periodic integrity audits.
