# Implementation Validation — Daily/H1 Named-Level Decomposition

Date: 2026-08-08
Study: `DFXC-20260808-006-pivot-daily-level-decomposition`
Role: `implementation_operations`
Status: `DIAGNOSTIC_RECONSTRUCTION_VALIDATED_WITH_RECORDED_TERMINAL_LEDGER_RESIDUAL`

This is implementation-side validation, not independent `governance_release_assurance`.

## Cache/data integrity

- Dataset: Dukascopy FX Cash / `dukascopy_fx_cash_m1_bid_ask_v1`.
- Ten canonical pair archives restored from the permanent registered Google Drive cache.
- No historic market-data reacquisition was performed.
- Analysis window uses 2021 only for prior-day/ATR warm-up and 2022-2025 for diagnostic outcomes; 2026 is not used.

## Exact observation-geometry reconstruction

The reconstructed observation population matches the frozen `DFXC-20260808-003` holdout exactly:

- retained observations (`d <= 0.50`): 491,589 / 491,589;
- core strong denominator: 73,296 / 73,296;
- core weak denominator: 43,563 / 43,563;
- outer strong denominator: 83,336 / 83,336;
- outer weak denominator: 50,501 / 50,501.

This validates the restored M1 BID/ASK source, midpoint construction, UTC H1 aggregation, NY17 daily pivots, named-level assignment, local-spacing normalization, zone boundaries and wick classification.

## Terminal-ledger reconstruction limitation

The original heavy terminal ledger was not retained in the public repository. The same limitation was previously recorded in the Fibonacci-substitution study.

Reference reconstruction:

- pooled all-level interaction: +1.124 pp;
- frozen holdout interaction: +1.084 pp;
- absolute interaction residual: +0.040 pp;
- reconstructed retained terminals: 62,143;
- frozen retained terminals: 57,863.

Therefore named-level terminal estimates are explicitly classified as reconstructed diagnostics rather than exact replay.

## Robustness to reconstruction semantics

Five detector-continuity/tie-handling sensitivity variants were evaluated without changing pivot formula, zones or wick thresholds.

The first-order-minus-second-order tier contrast remained positive in every variant:

- reference no-gap/strict-tie: +2.190 pp;
- gap-reset/strict-tie: +2.062 pp;
- no-gap/latest-tie: +2.199 pp;
- gap-reset/latest-tie: +2.067 pp;
- strict full-clock-gap ATR stress test: +1.668 pp.

This supports the qualitative mechanistic conclusion while preserving the exact-ledger limitation.

## Primary diagnostic

Reference reconstruction:

- S1/R1 interaction: +2.393 pp;
- S2/R2 interaction: +0.203 pp;
- difference: +2.190 pp;
- 5,000 pair-year clustered-bootstrap 95% CI: [+0.354,+3.961] pp;
- two-sided sign-mass p approximately 0.0176;
- positive pair deltas: 9/10;
- positive calendar-year deltas: 4/4.

No level-selection or trading authorization follows from this implementation validation.

## Remaining governance boundary

Independent assurance remains pending for this study and for relevant parent studies in the open pivot research stack.
