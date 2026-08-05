# Repository Control

## CACHE-FIRST CONTROL — MANDATORY AND HIGHEST PRIORITY

This instruction takes precedence over strategy-specific roadmaps, work packages, workflows and convenience.

The DTR project owns a qualified, permanent private Dukascopy FX cache. Before any historic FX download or strategy test, the operator or agent must:

1. consult `data/private_market_data_cache_registry.json`;
2. open the canonical Drive dataset folder `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`;
3. locate the requested pair and period;
4. restore and verify the registered archive using `scripts/restore_private_market_data_cache.py`;
5. reuse that data when the requested construction matches.

The permanent cache contains:

- EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP;
- Dukascopy M1 BID and ASK;
- complete years 2015 through 2025;
- 2026 YTD ending exclusive 2026-07-24;
- annual audits, pair manifests and SHA-256 evidence.

**Full historic redownload is prohibited.**

Permitted acquisition exceptions:

- a registered part or archive fails checksum and no intact copy can be recovered;
- the requested pair, year or side is genuinely absent;
- the user requests an incremental extension after the registered end date;
- the study requires a different source construction, such as ticks, depth, a different timeframe, or different side semantics.

Every exception requires a pre-acquisition record explaining why the permanent cache is insufficient. Every successful acquisition must be added to the permanent cache, checksummed, registered and verified before temporary copies are removed.

See `docs/PERMANENT_MARKET_DATA_CACHE.md` for the complete storage, restore and governance contract.

## Repository-wide decision hierarchy

1. Data provenance, integrity and cache reuse.
2. Causal event and execution semantics.
3. Preregistration and sample-boundary protection.
4. Scientific decision gates.
5. Strategy construction and cost stress.
6. Pine parity, alerts, paper deployment and live-readiness.

A downstream decision may not override an upstream failure.

## Source-of-truth files

- Agent entrypoint: `AGENTS.md`
- Repository control: `REPOSITORY_CONTROL.md`
- Current project status: `STATUS.md`
- Roadmap: `ROADMAP.md`
- Changelog: `CHANGELOG.md`
- Dataset catalog: `data/catalog.yaml`
- Private FX cache registry: `data/private_market_data_cache_registry.json`
- Permanent cache runbook: `docs/PERMANENT_MARKET_DATA_CACHE.md`

## Data security boundary

- The GitHub repository is public.
- Raw market data stays in private storage.
- Repository files may contain Drive folder identifiers and checksums, but not raw candles or credentials.
- The canonical Drive folder was verified private and not shared on 2026-08-06.
- GitHub Actions artifacts are temporary recovery sources, not permanent storage.

## Maintenance obligations

Any change to cache location, permissions, coverage, schema, archive composition or checksum requires:

- registry version increment;
- `CHANGELOG.md` entry;
- `STATUS.md` update;
- restore verification;
- update of the permanent cache runbook.
