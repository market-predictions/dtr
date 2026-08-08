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

## DUKASCOPY FX CASH RESEARCH MEMORY — MANDATORY

The canonical research name for the registered ten-pair source is **Dukascopy FX Cash**. Its machine research ID is `dukascopy_fx_cash_m1_bid_ask_v1`; the legacy catalog key remains valid for backward compatibility.

Before defining a new test on this dataset, the operator or agent must read `research_registry/DUKASCOPY_FX_CASH_RESEARCH_STANDARD.md` and search `research_registry/dukascopy_fx_cash/INDEX.md` for prior work on the same hypothesis, mechanism, level, filter or strategy family.

A Dukascopy FX Cash study is not durably complete until the central research registry preserves:

- the exact market question, null/alternative and mechanism;
- pair universe, data windows, price basis, session/time rules and holdout state;
- event/reset/overlap definitions and the primary endpoint;
- baseline/placebo/falsification design and selection family;
- inference and execution assumptions;
- exact programme decision, negative findings, limitations and prohibited rescue paths;
- exact repository ref, immutable 40-character commit SHA and evidence paths;
- independent assurance status where applicable.

Detailed implementation and heavy evidence may remain on strategy/research branches. The registry on the durable project line is the lookup and scientific-memory layer and must freeze the exact producing commit rather than relying on a mutable branch head or chat history.

Run `python scripts/validate_dukascopy_fx_cash_registry.py` before treating registry work as complete.

## Repository-wide decision hierarchy

1. Data provenance, integrity and cache reuse.
2. Research-memory recovery and prior-test lookup for Dukascopy FX Cash.
3. Causal event and execution semantics.
4. Preregistration and sample-boundary protection.
5. Scientific decision gates.
6. Strategy construction and cost stress.
7. Pine parity, alerts, paper deployment and live-readiness.

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
- Dukascopy FX Cash research standard: `research_registry/DUKASCOPY_FX_CASH_RESEARCH_STANDARD.md`
- Dukascopy FX Cash research index: `research_registry/dukascopy_fx_cash/index.json`

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

Any material Dukascopy FX Cash study requires a new immutable `DFXC-*` study ID unless it is a deterministic rerun of an unchanged frozen study. Negative results must remain searchable. A rejected study may not be cosmetically renamed and rerun as new discovery work without explicitly linking the prior rejection and defining a genuinely new hypothesis or mechanism.
