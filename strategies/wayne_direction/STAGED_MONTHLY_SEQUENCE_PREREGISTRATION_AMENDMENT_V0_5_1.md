# Staged Monthly Sequence — Preregistration Amendment v0.5.1

Date frozen: 2026-07-27
Parent: `STAGED_MONTHLY_SEQUENCE_PREREGISTRATION_V0_5.md`
Status: authoritative pre-outcome clarification

No real-data staged-sequence outcome had been opened when this amendment was committed.

## Central-pivot boundary

For the primary `CLOSE_IN_ZONE` rule:

- bullish location is `M2 <= price < P`;
- bearish location is `P < price <= M3`;
- an exact close or month open at P alone is a neutral boundary and creates neither primary side.

For the labeled `RANGE_TOUCH` sensitivity, a bar spanning P may create both side-specific opportunities. Both remain in the same instrument-month statistical cluster.

## Available-treatment inference floor

The sample gates in v0.5 are supplemented by target-availability floors:

- primary day 5: at least 30 conservative-target treatment observations must remain available at the fixed landmark;
- day-10 sensitivity: at least 40 conservative-target treatment observations must remain available at the fixed landmark.

Targets touched before or on the landmark remain pre-consumed and do not count toward these floors.

## Breadth effect eligibility

Pair-level and year-level treatment-control effects are classified as positive or negative only when the stratum contains at least three available treatment and three available control observations. Smaller strata are reported but cannot satisfy breadth gates.

## Unchanged boundaries

All other v0.5 definitions, statistical tests, promotion requirements and protected boundaries remain unchanged.
