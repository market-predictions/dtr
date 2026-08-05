# Cross-Pair Stage-1 Replication Preregistration

Date: 2026-08-05

## Question

Do canonical 250-pip Large Quarter Points produce greater short-horizon continuation than roundness-matched 50/100-pip levels in EUR/USD and USD/JPY?

## Instruments and quote scaling

- EUR/USD: pip size 0.0001.
- USD/JPY: pip size 0.01.
- All thresholds remain expressed in pips: 50-pip candidate lattice, 250-pip canonical cycle, 25-pip rearm distance and 10-pip first-passage barrier.

## Sample

- Development: 2015-01-01 through 2019-12-31.
- Internal validation: 2020-01-01 through 2021-12-31.
- Later data must not be processed during this work package.

## Primary estimate

Matched canonical phase-0 minus pooled noncanonical phase return at 60 minutes, matched within year, crossing direction, whole/half-100 roundness and four-hour UTC session.

## Decision rule

- If both pair replications are null/negative, demote the canonical 250-pip theory and stop before transition/strategy work.
- If one pair is convincingly positive and stable across development and validation, investigate pair-specific quote conventions only.
- If both pairs are positive and stable, authorize the longer-horizon transition census.

No thresholds or filters may be changed after pair outcomes are observed.
