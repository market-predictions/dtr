# Work Package — Pivot Multiscale Terminal + Wick Rejection

Date: 2026-08-08
Work package: `PIV-WP-20260808-03`
Role: `implementation_operations`
State: `ACTIVE_PREREGISTERED`

## Objective

Test whether scale-aligning directional-leg termination to pivot horizon reveals a robust pivot-proximity terminal-hazard effect, then conditionally test whether directionally appropriate wick rejection is an observable exhaustion signature that adds information specifically inside the pivot core.

## Scientific units

1. `DFXC-20260808-001-pivot-multiscale-terminal` — primary structural/falsification study.
2. `DFXC-20260808-002-pivot-wick-rejection` — conditional mechanism study, eligible only on mappings passing Study 1.

Both preregistrations were frozen on branch `agent/pivot-multiscale-terminal-wick` before new outcomes were computed.

## Scope

- Ten-pair Dukascopy FX Cash universe.
- Development 2015-2019; internal validation 2020-2021.
- Scale map D/H1, W/H4, M/D1, Q/W1, Y/MN1.
- Classic floor pivots and inherited normalized 0-20% core versus 30-50% outer geometry.
- Pivot-blind ATR24 directional-change endpoint detector at each mapped leg timeframe.
- Conditional wick-rejection interaction using candle geometry known at candle close.
- Cluster-bootstrap inference, multiplicity control, pair breadth and leave-one-pair-out falsification.

## Non-scope

- Protected 2022-2025 holdout.
- Volume/tick-activity confirmation.
- Execution P&L, entries, stops, targets, Pine, alerts, sizing, paper trading or deployment.
- Post-outcome threshold, pair, level, session or timeframe optimization.

## Acceptance criteria

- Preregistrations committed before outcome computation.
- Cache identities verified; no reacquisition of registered history.
- Analysis code hard-fails on timestamps >= 2022-01-01.
- Exact resampling and endpoint semantics covered by tests.
- Study 1 reports all five mappings, including negative results.
- Study 2 runs only for frozen Study-1 survivors and reports generic-wick versus pivot-specific interaction decomposition.
- 5,000-draw final bootstrap and Holm family correction are applied.
- Results, limitations, authorized next steps and prohibited rescue paths are registered in the Dukascopy FX Cash Research Registry.
- Implementation candidate receives independent `governance_release_assurance` before merge.

## Evidence plan

Persist compact machine results, human reports, deterministic evidence manifests, source commit references and validation tests. Heavy raw market data and large intermediate ledgers remain private/uncommitted.

## Holdout boundary

`2022-01-01` through `2025-12-31` remains `UNOPENED`. This work package has no authority to consume it.
