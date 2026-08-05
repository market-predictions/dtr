# Work Package — Cross-Pair Stage-1 Replication

- **ID:** QT-WP-20260805-02
- **Status:** Active
- **Owner:** autonomous research agent
- **Parent:** QT-WP-20260805-01 / PR #66

## Objective

Replicate the frozen Stage-1 Large Quarter Point distinctiveness test on EUR/USD and one JPY-quoted pair (USD/JPY) before any strategy-level work.

## Frozen design

- Dukascopy M1 bid/ask data.
- Development: 2015–2019.
- Internal validation: 2020–2021.
- 2022–2025 remains unopened.
- Mid-close crossing of 50-pip lattice levels.
- Canonical phase: 0 modulo 250 pips.
- Controls: 50, 100, 150 and 200 modulo 250 pips.
- Rearm/reset: 25 pips.
- Primary endpoint: direction-aligned 60-minute midpoint return.
- Matching strata: year, direction, whole/half-100 roundness, four-hour UTC session.
- Uncertainty: year-preserving weekly block bootstrap.

## Acceptance gates

1. Acquisition and audit complete for both bid and ask.
2. Generic engine reproduces the GBP/USD contract without changing its semantics.
3. EUR/USD and USD/JPY run with pair-appropriate pip size and unchanged pip-domain thresholds.
4. Report development, validation and combined estimates separately.
5. No strategy optimization or holdout opening.

## Deliverables

- generic Dukascopy bid/ask downloader;
- pair-aware Stage-1 engine and runner;
- synthetic JPY scaling and backward-compatibility tests;
- GitHub Actions replication workflow;
- compact pair result artifacts;
- cross-pair research report and roadmap decision.
