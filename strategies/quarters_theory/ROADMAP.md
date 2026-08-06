# Quarters Theory Roadmap

**Version:** 0.3.0  
**Updated:** 2026-08-05  
**Status:** Stage 1 complete for GBP/USD; Gate 0 not passed

## Research objective

Determine whether canonical 250-pip Large Quarter Points provide stable, economically meaningful information beyond generic round-number and momentum effects. Strategy P&L is downstream and is prohibited until the structural claim survives.

## Stage 0 — Source fidelity and governance

- [x] Separate the grid-only hypothesis from Yotov's broader discretionary methodology.
- [x] Record the original 25/75/125/225-pip ladder as a hypothesis rather than a law.
- [x] Obtain and assess an adversarial second opinion.
- [x] Incorporate barrier-null, roundness-control, power and execution criticisms.
- [x] Preserve 2022-2025 as outcome-unopened holdout; metadata/schema inspection only.
- [ ] Verify the exact faithful book trade stop rule from the primary source before coding F0.

## Stage 1 — Cheap distinctiveness screen

### QT-00 Data audit

- [x] Validate 2015-2021 GBP/USD Dukascopy M1 bid/ask archive.
- [x] Verify annual checksums, row counts, timestamps and non-negative spreads.
- [x] Record 3,682,080 calendar-minute rows and 2,612,846 active quote minutes.

### QT-01 Round-level engine

- [x] Generate every 50-pip level.
- [x] Identify canonical phase 0 modulo 250 pips.
- [x] Classify whole-100 and half-100 roundness.
- [x] Use close-based crossing and per-level/direction reset state.
- [x] Add deterministic synthetic tests.

### QT-B Short-horizon crossing study

- [x] Evaluate 5, 15, 30, 60, 120, 240 and 1,440-minute directional outcomes.
- [x] Compare canonical LQPs with other 50-pip phases inside matched year, direction, roundness and session strata.
- [x] Run year-preserving weekly block bootstrap.
- [x] Run adjusted return regressions and +10/-10-pip first-passage models.
- [x] Run reset, overshoot and spread sensitivities.

### QT-C Encompassing interpretation

- [x] Evaluate whether LQP status adds positive short-horizon information beyond roundness-matched controls.
- [x] Gate 0 decision for GBP/USD: **not passed**.
- [ ] Replicate Stage 1 on EUR/USD and a JPY pair before deciding whether the grid family is globally demoted.

## Stage 2 — Episode census and power

Status: **deferred** pending cross-pair Stage-1 replication.

- [ ] Build the 25/75/125/225 first-passage state machine.
- [ ] Align structural rejection with executable stop boundaries.
- [ ] Estimate real episode counts and cross-pair dependence.
- [ ] Freeze minimum detectable and minimum economically useful effects.

## Stage 3 — Structural transition tests

Status: **blocked by Gate 0 unless cross-pair evidence reverses the conclusion**.

- [ ] Test P75-to-P225 excess over matched timed null.
- [ ] Test P125 incremental information.
- [ ] Evaluate target, rejection and timeout jointly.
- [ ] Compare FX-clock and realised-volatility time.
- [ ] Test the three-day rule as a survival/hazard claim.

## Stage 4 — Frozen strategy candidates

Status: **not authorized**.

- [ ] F0 faithful book Large Quarter Trade.
- [ ] C1 +75 acceptance continuation.
- [ ] C2 +125 half-point confirmation.
- [ ] C3 accepted-transition pullback.
- [ ] R1 failed-overshoot rejection.

No trend, candle, session, macro or regime filter may be introduced before structural survival. A filter cannot rescue a level hypothesis that has no standalone incremental content.

## Stage 5 — Costs, holdout and replication

- [ ] Executable bid/ask backtests.
- [ ] Spread, slippage and financing stress.
- [ ] Joint cross-pair calendar-block resampling.
- [ ] Pair/year leave-one-out analysis.
- [ ] One-time 2022-2025 holdout opening.
- [ ] Independent code-path replication.

## Decision policy

Continue structural research only when canonical LQP status is positive against roundness-matched controls, stable across development and validation, not dependent on one pair or event-quality definition, and large enough to remain relevant after execution costs.

Demote or stop when canonical levels are ordinary relative to matched 50/100-pip levels, any advantage is explained by generic momentum or event composition, positive results depend on one reset/horizon/pair, or costs dominate the upper confidence bound.

A well-supported negative conclusion is a successful research outcome.
