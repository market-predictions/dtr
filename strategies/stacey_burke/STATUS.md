# Stacey Burke FX Research Status

Date: 2026-07-24  
Version: `v0.1.1-incremental-source-retention`  
Active work package: `SB-WP-20260724-01`  
State: `SOURCE_ACQUISITION_RECOVERY_ACTIVE_PERFORMANCE_BLOCKED`

## Current objective

Build a qualified, reusable Dukascopy BID/ASK M1 source universe for a multi-asset Stacey Burke event census.

## Fixed universe

EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP.

## Fixed source period

- 2015–2021: mechanism discovery census.
- 2022–2023: event-study validation.
- 2024–2025: untouched holdout.
- 2026 YTD through 2026-07-23: monitoring only.

## Retention and gating semantics

- Every completed pair is preserved independently as a private source artifact.
- A successfully acquired pair is cached before source qualification is enforced.
- Qualification evidence is uploaded even when a pair fails a source gate.
- A failed or missing pair does not delete or suppress artifacts from completed pairs.
- All ten mandatory pairs remain required only for authorization of the pooled event census.

## Current authorization

Authorized:

- private source acquisition;
- incremental pair-level source retention;
- source integrity qualification;
- BID/ASK synchronization and spread audits;
- annual hash freezing;
- compact source evidence.

Blocked:

- event-return inspection before the complete source freeze;
- strategy entries and P&L;
- pair selection by result;
- pair-specific parameters;
- SB-1/SB-2/SB-3 execution;
- Pine, sizing, alerts, paper deployment and live use.
