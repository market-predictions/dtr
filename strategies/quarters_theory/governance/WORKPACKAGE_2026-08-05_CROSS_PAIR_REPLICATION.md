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

## Source contract

Reuse the already qualified Stacey Burke ten-pair Dukascopy universe from workflow run `30129064261`. The EURUSD and USDJPY artifacts contain annual BID and ASK M1 files for 2015–2025 plus 2026 YTD and are retained through 2026-10-22.

The workflow must:

1. restore the retained artifact rather than download Dukascopy again;
2. validate every annual raw-source SHA256 against its embedded audit;
3. process only 2015–2021;
4. leave 2022–2025 and 2026 YTD unopened for this hypothesis;
5. fail closed if the retained source cannot be authenticated.

## Implementation contract

The frozen GBP/USD engine itself is not generalized or rewritten. A deterministic adapter converts the retained source schema and normalizes each quote so one source pip equals `0.0001` in the existing engine:

- EUR/USD scale: `1.0`;
- USD/JPY scale: `0.01`.

This preserves every signal, event, reset, matching and bootstrap code path used for GBP/USD and removes implementation drift as a replication confound.

## Acceptance gates

1. Retained source restored and authenticated for both bid and ask.
2. No Dukascopy reacquisition in the normal replication path.
3. No change to the frozen Stage-1 engine.
4. Tests prove EUR/USD identity scaling and USD/JPY pip-equivalent scaling.
5. Report development, validation and combined estimates separately.
6. No strategy optimization or holdout opening.

## Deliverables

- authenticated retained-source restoration workflow;
- checksum-preserving schema and pip-domain normalization adapter;
- unchanged frozen Stage-1 runner;
- EUR/USD and USD/JPY normalization tests;
- compact pair result artifacts;
- cross-pair research report and roadmap decision;
- durable-cache governance follow-up before source-artifact expiry.
