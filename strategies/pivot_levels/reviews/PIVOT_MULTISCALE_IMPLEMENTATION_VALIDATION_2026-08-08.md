# Pivot Multiscale / Wick — Implementation Validation

Date: 2026-08-08  
Work package: `PIV-WP-20260808-03`  
Role: `implementation_operations`  
Status: `IMPLEMENTATION_VALIDATION_PASS / GOVERNANCE_ASSURANCE_PENDING`

## Scope

This record documents internal implementation validation only. It is **not** an independent `governance_release_assurance` decision and must not be cited as one.

## Data integrity

- All 22 registered split files for the ten Dukascopy FX Cash archives matched their canonical SHA-256 values.
- Each reconstructed pair archive was hashed before use and matched the permanent cache registry.
- The analysis opened only BID/ASK annual members 2015–2021.
- Aggregated scientific ledgers contain years 2015 through 2021 only.
- The protected 2022–2025 holdout was not opened.

## Coverage

- Pairs: 10/10 canonical Dukascopy FX Cash pairs.
- Primary mappings: D/H1, W/H4, M/D1, Q/W1, Y/MN1.
- Scale-mismatch benchmarks: W/H1, M/H1, Q/H1, Y/H1.
- Every pair contains all nine mapping records.

## Anti-circularity check

A synthetic sequence was run through the frozen endpoint detector. A detector candle made a new high and closed with a very large upper wick. The candidate high was verified **not** to self-confirm on that candle. After a later detector candle closed beyond the lagged-ATR reversal threshold, the earlier high was then marked terminal.

Result: `PASS`.

This confirms the Amendment-02 rule operationally separates candidate wick geometry from later terminal confirmation.

## Separate arithmetic recalculation

A separate calculation path, without importing the primary effect helper, re-read the per-pair aggregated count ledgers and recomputed:

- all five Study-1 combined `core terminal rate - outer terminal rate` effects;
- both Study-2 eligible difference-in-differences wick interactions;
- year-range and pair/mapping completeness invariants.

All recomputed values matched the persisted results to machine precision.

Result: `PASS_EXACT`.

## Scientific gates reproduced

Study 1:

- D/H1: PASS.
- W/H4: PASS.
- M/D1: FAIL.
- Q/W1: FAIL.
- Y/MN1: FAIL.

Study 2 conditional eligibility was frozen to `[D_H1, W_H4]` before inspecting wick outcomes.

Study 2:

- D/H1 pivot-specific wick interaction: PASS.
- W/H4 pivot-specific wick interaction: FAIL.

## Remaining assurance boundary

An independent reviewer must still reconstruct the candidate from the frozen preregistrations, compact results, report and evidence manifest and return `PASS | FAIL | INDETERMINATE` before this branch is treated as governance-assured.

No holdout opening, strategy implementation, Pine conversion, alerting, sizing or live-trading action is authorized by this implementation validation.
