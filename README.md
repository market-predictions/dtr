# DTR Optimization Lab

Python research and validation framework for the Daytrading Rauf (DTR) TradingView strategy.

## Purpose

The project reproduces the DTR decision pipeline outside TradingView so that strategy components can be tested systematically rather than by manually changing Pine inputs one at a time.

The research workflow is:

1. validate and normalize market data;
2. reproduce the Pine baseline closely enough for trade-level parity;
3. instrument the complete setup funnel and rejection reasons;
4. run controlled experiment packs for sweep, BOS/MSS, entry, regime, calendar, and exit logic;
5. validate candidates with chronological walk-forward testing, cost stress, and parameter-neighbourhood checks;
6. port only robust candidates back to Pine for final TradingView Strategy Tester validation.

## Current scope

The first dataset is one-minute NQ futures data covering part of December 2022 through December 2025. It will be used to build and validate the framework. NQ-specific conclusions will not automatically be transferred to GBPUSD or other markets.

The first research milestone is not optimization. It is **baseline parity and funnel attribution**.

## Data policy

Raw market datasets and generated research artifacts are not committed to normal Git history.

Place local files under:

```text
data/raw/
data/processed/
artifacts/
reports/
```

These directories are excluded by `.gitignore`. Dataset provenance, checksums, schema, and validation findings are committed under `data/catalog.yaml` and `docs/`.

## Planned structure

```text
configs/              experiment configuration
data/                 catalog and local data locations
docs/                 architecture, audits, and methodology
scripts/              command-line entry points
src/dtr_lab/           reusable research package
tests/                 deterministic unit and parity tests
```

## Operating principles

- No optimization before baseline parity is credible.
- No ranking by net profit alone.
- Every filter must report both performance effect and opportunity coverage.
- Entry and exit modules are tested separately before combinations.
- Chronological holdout data remains untouched until candidate selection.
- Parameter plateaus are preferred over sharp optima.
- TradingView remains the final execution reference.

## Status

Repository initialized for **v0.1.0 — Dataset Audit and Baseline Architecture**.
