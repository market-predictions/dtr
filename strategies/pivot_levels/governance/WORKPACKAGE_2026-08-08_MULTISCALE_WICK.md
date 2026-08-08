# Work Package — Pivot Multiscale Terminal + Wick Rejection

Date: 2026-08-08
Work package: `PIV-WP-20260808-03`
Role: `implementation_operations`
State: `IMPLEMENTATION_COMPLETE_ASSURANCE_PENDING`

## Objective

Test whether scale-aligning directional-leg termination to pivot horizon reveals a robust pivot-proximity terminal-hazard effect, then conditionally test whether directionally appropriate wick rejection is an observable exhaustion signature that adds information specifically inside the pivot core.

## Scientific units

1. `DFXC-20260808-001-pivot-multiscale-terminal` — primary structural/falsification study.
2. `DFXC-20260808-002-pivot-wick-rejection` — conditional mechanism study, eligible only on mappings passing Study 1.

Both preregistrations were frozen on branch `agent/pivot-multiscale-terminal-wick` before new outcomes were computed. Two pre-outcome amendments fixed implementation details and prohibited same-candle endpoint self-confirmation before wick outcomes were observed.

## Scope executed

- Ten-pair Dukascopy FX Cash universe.
- Development 2015-2019; internal validation 2020-2021.
- Scale map D/H1, W/H4, M/D1, Q/W1, Y/MN1.
- Classic floor pivots and inherited normalized 0-20% core versus 30-50% outer geometry.
- Pivot-blind ATR24 / 0.75 ATR directional-change endpoint detector at each mapped leg timeframe.
- Conditional wick-rejection interaction using candle geometry known at candle close.
- Pair-year clustered bootstrap, Holm correction, pair breadth, leave-one-pair-out and named-level falsification.

## Non-scope preserved

- Protected 2022-2025 holdout.
- Volume/tick-activity confirmation.
- Execution P&L, entries, stops, targets, Pine, alerts, sizing, paper trading or deployment.
- Post-outcome threshold, pair, level, session or timeframe optimization.

## Acceptance results

- PASS — preregistrations committed before outcome computation.
- PASS — all 22 registered cache split identities verified; all ten reconstructed pair archives verified.
- PASS — analysis exposure limited to 2015-2021; result ledgers contain no 2022+ year.
- PASS — anti-circularity unit check proves a large-wick endpoint candidate cannot self-confirm on the same detector candle.
- PASS — Study 1 reports all five mappings and all four frozen H1 mismatch benchmarks.
- PASS — Study 2 eligibility frozen to D/H1 and W/H4 before wick outcomes.
- PASS — 5,000-draw pair-year bootstrap and Holm family correction applied.
- PASS — separate arithmetic calculation reproduced primary effects exactly.
- PASS — results, limitations, authorized next steps and prohibited rescue paths registered in the Dukascopy FX Cash Research Registry.
- PENDING — independent `governance_release_assurance` on the exact candidate before merge/closeout.

## Scientific result

Study 1:

- D/H1 PASS: +1.02 pp terminal enrichment, 95% CI [+0.85,+1.20], 10/10 pairs positive.
- W/H4 PASS: +0.67 pp, 95% CI [+0.33,+1.01], 8/10 pairs positive; stronger than W/H1 benchmark +0.28 pp.
- M/D1 FAIL.
- Q/W1 FAIL.
- Y/MN1 FAIL.

Study 2:

- D/H1 pivot-specific wick interaction PASS: +0.92 pp, 95% CI [+0.49,+1.36], 8/10 pairs positive, all leave-one-pair-out positive.
- W/H4 wick interaction FAIL: +0.77 pp, 95% CI [-0.07,+1.59], p=0.0744.

## Evidence

- `strategies/pivot_levels/results/2026-08-08/pivot_multiscale_terminal_summary.json`
- `strategies/pivot_levels/results/2026-08-08/pivot_wick_rejection_summary.json`
- `strategies/pivot_levels/results/2026-08-08/pivot_multiscale_evidence_manifest.json`
- `strategies/pivot_levels/reports/PIVOT_MULTISCALE_TERMINAL_WICK_REPORT_2026-08-08.md`
- `strategies/pivot_levels/reviews/PIVOT_MULTISCALE_IMPLEMENTATION_VALIDATION_2026-08-08.md`
- `claims/PIV-WP-20260808-03.md`
- `handovers/PIV-WP-20260808-03.md`

## Holdout boundary

`2022-01-01` through `2025-12-31` remains `UNOPENED`. This work package has no authority to consume it. The strongest next protected-confirmation candidate is the unchanged Daily/H1 pivot-core wick interaction, subject to independent assurance and the applicable holdout authorization.
