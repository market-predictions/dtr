# Quarters Theory Ten-Pair Universe Confirmation Preregistration

Date: 2026-08-06  
Work package: `QT-WP-20260806-03`

## Prior evidence and binding status

The canonical 250-pip Large Quarter Point hypothesis failed the frozen GBPUSD Stage-1 test. The unchanged EURUSD and USDJPY replications also failed stability: both showed positive development estimates and negative 2020–2021 validation estimates. The binding programme status before this universe run is therefore:

`DEMOTE_CANONICAL_250_PIP_THEORY`

This ten-pair run is confirmatory. It cannot retrospectively rescue that failed gate or authorize strategy construction.

## Question

Across the registered ten-pair Dukascopy FX Cache, do canonical phase-0 levels modulo 250 pips exhibit a positive and temporally stable 60-minute continuation effect relative to roundness-matched 50-pip lattice controls?

## Source

- Dataset shorthand: `Dukascopy FX Cache`.
- Canonical private Drive folder ID: `160qGdjm9Gi6pr05nRHuUXaTZc9EgJOOU`.
- Temporary workflow transport: checksum-identical retained source artifacts from run `30129064261`.
- Format: Dukascopy M1, separate BID and ASK, UTC.
- No historical reacquisition is authorized.

## Instruments

EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP.

Reference pairs already studied: GBPUSD, EURUSD, USDJPY.

New confirmation panel: USDCHF, AUDUSD, NZDUSD, USDCAD, EURJPY, GBPJPY and EURGBP.

## Frozen sample boundaries

- Development: 2015-01-01 through 2019-12-31.
- Internal validation: 2020-01-01 through 2021-12-31.
- 2022–2025 outcomes remain unopened.
- 2026 remains monitoring-only and is not processed.

## Frozen engine

No signal or estimator change is permitted:

- candidate lattice every 50 pips;
- canonical phase 0 modulo 250 pips;
- controls at phases 50, 100, 150 and 200;
- midpoint close crossing;
- directional rearm after a 25-pip return to the origin side;
- primary endpoint: direction-aligned midpoint return after 60 minutes;
- matching: year, direction, whole/half-100 roundness and four-hour UTC session;
- uncertainty: 5,000-draw year-preserving weekly block bootstrap;
- JPY quotes normalized by 0.01 so one source pip equals 0.0001 in the unchanged engine.

GBPUSD must exactly reproduce the frozen reference event counts and development, validation and combined point estimates. Failure is a source/adapter parity stop, not a scientific result.

## Pair qualification

A pair is `positive_stable` only when:

1. development point estimate is positive;
2. validation point estimate is positive;
3. combined 2015–2021 bootstrap 95% interval excludes zero on the positive side.

## Binding confirmation decision

The reference-pair demotion remains binding in every outcome.

- 0 positive/stable pairs among the seven new confirmation pairs:
  `CONFIRM_GLOBAL_DEMOTION_NO_PAIR_EXCEPTIONS`.
- 1–2 positive/stable confirmation pairs:
  `GLOBAL_DEMOTION_STANDS_ISOLATED_PAIR_EXCEPTIONS_ONLY`.
- 3 or more positive/stable confirmation pairs:
  `GLOBAL_DEMOTION_STANDS_UNEXPECTED_BREADTH_REQUIRES_NEW_PREREGISTRATION`.

No outcome directly authorizes transition studies, entry logic, targets, costs, P&L, Pine, alerts, sizing or deployment.

## Descriptive diagnostics

Report, without changing the binding rule:

- pair event and LQP counts;
- development, validation and combined effects;
- combined 95% interval;
- counts of positive development, validation and combined effects;
- development-to-validation sign flips;
- median combined pair effect;
- positive/stable pair breadth.
