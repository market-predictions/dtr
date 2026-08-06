# Work Package — Quarters Theory Ten-Pair Universe Confirmation

- **ID:** `QT-WP-20260806-03`
- **Status:** Active
- **Owner:** autonomous research agent
- **Parent:** `QT-WP-20260805-02` / PR #67
- **Priority:** Scientific closeout before any strategy-level work

## Objective

Run the unchanged Quarters Theory Stage-1 distinctiveness test across the full registered ten-pair Dukascopy FX Cache and classify whether the already-demoted canonical 250-pip hypothesis has no exceptions, isolated pair exceptions or an unexpected breadth anomaly.

## Data control

- Use the `Dukascopy FX Cache`; do not reacquire historical data.
- Verify every annual source checksum before processing.
- Process only 2015–2021.
- Preserve 2022–2025 outcome blindness.
- Raw candles remain outside Git.

## Frozen scientific contract

The engine, thresholds, rearm state machine, horizons, matching strata and bootstrap remain unchanged from Stage-1. No pair, year, phase, session, spread, overshoot or reset selection is permitted after outcomes.

## Acceptance gates

1. Ten registered pairs present.
2. BID and ASK annual hashes pass.
3. GBPUSD exactly reproduces the frozen Stage-1 reference.
4. Every pair reports development, validation and combined estimates separately.
5. The preregistered confirmation decision is generated automatically.
6. No holdout opening or strategy optimization occurs.

## Deliverables

- ten pair evidence artifacts;
- machine-readable universe summary;
- client-readable universe report;
- status and changelog update;
- independent process review after the result is frozen.

## Restrictions

This work package cannot authorize transition logic, entries, stops, targets, execution P&L, Pine, alerts, sizing, paper trading or deployment. Any isolated exception requires a new independent preregistration and cannot amend the failed canonical-theory gate.
