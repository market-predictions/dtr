# Implementation Validation — Daily/H1 Holdout + Weekly/H4 Zone Geometry

Date: 2026-08-08
Work package: `PIV-WP-20260808-04`
Role: `implementation_operations`
Status: `IMPLEMENTATION_VALIDATION_PASS_ASSURANCE_PENDING`

This document is implementation-side validation only. It is **not** an independent `governance_release_assurance` PASS.

## Data integrity

- Canonical dataset: **Dukascopy FX Cash** / `dukascopy_fx_cash_m1_bid_ask_v1`.
- All 22 registered split source parts were previously verified against `data/private_market_data_cache_registry.json` and remained the source material for this run.
- Each of the ten reconstructed pair archives was SHA-256 checked against the canonical full-archive identity before analysis.
- No historical reacquisition occurred.
- Raw market data and heavy pair ledgers remain private/uncommitted.

## Boundary validation

Daily/H1 holdout:

- outcome years in final compact ledger: exactly `2022, 2023, 2024, 2025`;
- 2021 used only as source warm-up/prior-day construction;
- no 2026 member read;
- ten canonical pairs present.

Weekly/H4 geometry:

- outcome years in final compact ledger: exactly `2015..2021`;
- no Weekly/H4 2022–2025 outcome inspected;
- ten canonical pairs present.

## Deterministic parent-reference reproduction

The weekly robustness preregistration required the inherited 20%-spacing geometry to reproduce the parent result before challenger geometries could be accepted.

Two preliminary weekly runs were invalidated and documented separately:

1. `PIVOT_WEEKLY_H4_ZONE_GEOMETRY_IMPLEMENTATION_DEVIATION_01_2026-08-08.md` — M1 FX-date filtering versus H4 aggregation ordering.
2. `PIVOT_WEEKLY_H4_ZONE_GEOMETRY_IMPLEMENTATION_DEVIATION_02_2026-08-08.md` — four non-terminal observations on the floating-point 20% boundary caused by algebraically equivalent but numerically different comparisons.

After restoring the parent's normalized-distance boundary semantics, final `SP20_REF` reproduces exactly:

- parent structural effect: `0.0066856022635854995`;
- final structural effect: `0.0066856022635854995`;
- difference: `0.0`;
- parent wick interaction: `0.007736672031333339`;
- final wick interaction: `0.007736672031333339`;
- difference: `0.0`.

Only this final corrected weekly run supports the scientific decision.

## Independent arithmetic recomputation

A separate compact-ledger checker recomputed without using the final summary values as inputs:

- Daily/H1 holdout interaction;
- Daily/H1 structural core-minus-outer effect;
- Weekly `SP10` structural effect;
- Weekly `SP10` wick interaction;
- Weekly `SP20_REF` structural effect;
- Weekly `SP20_REF` wick interaction;
- holdout year boundaries;
- weekly internal-study year boundaries;
- ten-pair identity.

All numerical comparisons matched to tolerance `<1e-14` and all boundary checks passed.

Local validation record SHA-256:

`527a90efb3c342ccc4d1c9be54ca7bd189a42937545fa9c9086c36af3a85d5cf`

## Frozen result artifact identities

The full local machine outputs used to create the durable compact repository summaries had SHA-256 identities:

- `daily_h1_holdout_results.json`: `9ee5426efd6dee03fb05243a2d96876ee6d0ad03f0d987dd5f86fdb7910e38ca`
- `weekly_h4_zone_geometry_results.json`: `8b525ca4f3b90b59150112e35af958e60e7064f416c92645662baba6c6264df9`

The repository stores the decision-relevant machine summaries and the complete human report. Heavy per-pair observation ledgers are intentionally not committed to the public repository.

## Decision validation

### DFXC-20260808-003

All preregistered holdout gates pass:

- combined interaction > 0;
- 95% CI lower bound > 0;
- 2022–2023 > 0;
- 2024–2025 > 0;
- 10/10 pair interactions positive;
- all leave-one-pair-out pooled interactions positive;
- five-bin core wick gradient non-decreasing.

Implementation decision:

`CONFIRM_DAILY_H1_PIVOT_WICK_INTERACTION_ON_PROTECTED_HOLDOUT`

The Daily/H1 2022–2025 holdout is now consumed for this exact question.

### DFXC-20260808-004

All seven preregistered geometries are reported. Only `SP10` passes the joint structural + wick gate after separate seven-hypothesis Holm corrections and also satisfies the preregistered material-strength classification.

Implementation decision:

`WEEKLY_H4_ZONE_GEOMETRY_MATERIALLY_STRENGTHENS_PIVOT_WICK_INTERACTION`

Weekly/H4 2022–2025 outcomes remain uninspected in this study.

## Remaining gate

Independent `governance_release_assurance` must reconstruct the exact candidate, verify the data/holdout authority, reference reproduction, inference/gate application and registry state, and issue `PASS | FAIL | INDETERMINATE` before merge.
