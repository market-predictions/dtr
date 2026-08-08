# Dukascopy FX Cash Research Standard

## Purpose

This standard is the durable research-memory contract for every study that uses the registered ten-pair Dukascopy FX cash dataset in this repository.

The raw market data remains private and cache-first. The research registry stores the scientific memory around that data: what was asked, exactly what was tested, which data window was exposed, what controls were used, what happened, what was rejected, what may be tested next, and where the immutable evidence lives.

A study is not considered durably complete until it is registered here.

## Canonical dataset identity

Human-facing name: **Dukascopy FX Cash**.

Machine identifier: `dukascopy_fx_cash_m1_bid_ask_v1`.

The legacy catalog key `dukascopy_fx_m1_bid_ask_2015_2025_2026_ytd` remains valid for backward compatibility. New research records must use the canonical name and machine identifier above.

Dataset contract:

- provider: Dukascopy;
- market: OTC cash/spot FX quote data;
- base granularity: M1;
- quote sides: separate BID and ASK;
- source timezone: UTC;
- pairs: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP;
- durable cache: complete 2015–2025 plus 2026 YTD ending exclusive 2026-07-24;
- raw candles: private, never committed to this public repository;
- canonical provenance and hashes: `data/private_market_data_cache_registry.json`.

Dukascopy FX Cash is not a consolidated interdealer order book and must not be described as one.

## Research object model

A research programme may contain many studies. A study is the smallest durable scientific decision unit. Each study receives an immutable identifier:

`DFXC-YYYYMMDD-NNN-slug`

A materially changed hypothesis, endpoint, event definition, control, data partition or selection rule receives a new study ID. A deterministic rerun of an unchanged frozen study remains under the same study ID and receives a distinct run/evidence reference.

Every registered study has:

1. `study.json` — frozen methodology and provenance;
2. `result.json` — normalized outcome and decision, once results exist;
3. frozen links to full report, raw summary artifacts, code, work package, review and handover on the exact Git ref/commit that produced them;
4. one row in `dukascopy_fx_cash/index.json`;
5. one rendered row in `dukascopy_fx_cash/INDEX.md`.

Strategy-specific folders remain authoritative for detailed implementation and heavy result artifacts. The registry is an index and normalized scientific-memory layer, not a duplicate strategy repository.

## Mandatory methodology fields

Before outcome inspection, freeze as much of the following as applicable:

- market question and decision relevance;
- null and alternative hypothesis;
- proposed economic/market mechanism;
- study type: structural, event study, strategy, falsification, robustness, replication or holdout confirmation;
- pair universe and exclusions;
- exact development, internal-validation and protected-holdout windows;
- source/base timeframe and analysis/resampling timeframe;
- price basis: midpoint, bid, ask, or executable bid/ask;
- pip convention and quote normalization;
- session/day boundary and timezone handling;
- missing-data and unsafe-gap policy;
- event eligibility, reset/rearm and overlap rules;
- primary endpoint and economic effect size;
- controls, placebos and matched-null construction;
- candidate/variant count and selection family;
- uncertainty method, clustering/block unit and multiple-testing correction;
- transaction-cost, spread, slippage and same-bar ordering policy for strategy tests;
- preregistration status and exact source branch/commit.

For JPY pairs, one pip is 0.01. For the other registered pairs, one pip is 0.0001 unless a study explicitly documents a different quote-normalization layer.

## Required result fields

A completed study must preserve:

- exact programme decision;
- standardized scientific disposition;
- primary effect estimates and uncertainty;
- breadth across pairs, years, directions or regimes when relevant;
- robustness and falsification results;
- limitations and what the result does not establish;
- holdout state after the study;
- independent review/assurance status;
- authorized next steps;
- prohibited rescue steps;
- exact evidence locations and commit hashes.

Negative findings are permanent research assets. They must not be deleted, hidden or relabelled as inconclusive merely because the preferred hypothesis failed.

## Scientific dispositions

Use one of:

- `SUPPORTED_INTERNAL`
- `PROMOTE_TO_HOLDOUT_CONFIRMATION`
- `REJECT_NO_INCREMENTAL_VALUE`
- `REJECT_MECHANISM`
- `DESCRIPTIVE_ONLY`
- `HOLD_FOR_FRESH_DATA`
- `INDETERMINATE`
- `INVALIDATED_DATA`
- `SUPERSEDED`
- `ABANDONED`

The exact historical decision string is preserved separately.

## Lifecycle

Use one of `DESIGN`, `PREREGISTERED`, `RUN_COMPLETE`, `INTERNAL_ASSURANCE_PASS`, `HOLDOUT_CONFIRMED`, `REJECTED`, `SUPERSEDED`, or `ABANDONED`.

Lifecycle is not scientific disposition. A rejected study can be complete and high quality.

## Holdout discipline

Each study declares its own partition contract. A commonly used FX split is development 2015–2019, internal validation 2020–2021 and protected holdout 2022–2025, but this is not silently imposed on unrelated studies.

Opening protected data requires an explicit authorization record. The registry validator rejects a study that says it opened a holdout without such a record. A holdout is consumed for the exact preregistered question tested; later related studies must state prior exposure.

## Falsification-first rule

Absolute hit rates are not enough. Studies about special levels, time windows, patterns or state variables must define a credible null/placebo whenever feasible. Examples include pivots versus shifted coordinates, Quarters versus phase-shifted/generic round-number controls, entry filters versus an unchanged baseline trade set, and signal grades versus shuffled or matched cohorts.

A claim survives only to the extent that it beats the relevant null and remains economically meaningful.

## Branch-resident evidence

Research evidence may live on a feature/research branch. This is a supported first-class state. Every completed registry entry freezes repository, Git ref, exact 40-character commit SHA and authoritative paths. The registry is intended to live on `main` after assurance even when detailed study code remains branch-resident. Future researchers must follow the frozen commit, not the mutable branch head.

## Completion gate

For a Dukascopy FX Cash study, done means:

1. dataset/cache identity verified;
2. methodology frozen or deviations logged;
3. run completed or stop reason recorded;
4. normalized result written;
5. positive and negative findings retained;
6. evidence paths frozen to an exact commit;
7. holdout state recorded;
8. assurance state recorded;
9. master index updated;
10. registry validation passes.

Run:

```bash
python scripts/validate_dukascopy_fx_cash_registry.py
```

The regular repository test suite also validates the registry.

## Reuse rule

Before starting a new Dukascopy FX Cash study, search `research_registry/dukascopy_fx_cash/INDEX.md`, inspect related study/result records, follow frozen evidence links, and explicitly classify the new work as replication, extension, contradiction, robustness, falsification or a new mechanism. Do not rerun a rejected hypothesis under a cosmetic rename.
