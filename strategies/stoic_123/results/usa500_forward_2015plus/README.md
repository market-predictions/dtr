# USA500 RTH Full 1-2-3 Forward Validation, 2015+

Decision: `REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`

This compact folder contains the frozen 2015–2025 decision evidence and 2026 YTD monitoring result for the unchanged Dukascopy USA500 RTH full 1-2-3 long-only candidate without a map or EMA200 filter.

## Decision blocks

- 2015–2019 primary forward: 177 trades, `-57.98R`, `-0.328R` expectancy.
- 2020–2022 crisis/regime: 134 trades, `+3.12R`, `+0.023R` expectancy.
- 2023–2025 recent holdout: 148 trades, `+10.55R`, `+0.071R` expectancy.
- Combined 2015–2025: 459 trades, `-44.31R`, `-0.097R` expectancy.
- 2026 YTD monitoring only: 29 trades, `+4.27R`, `+0.147R` expectancy.

Only 6 of 19 frozen gates passed. The primary confidence interval was wholly negative; cost stress and matched controls failed. The source is a Dukascopy bid-CFD proxy, not CME ES futures. Raw market data are not included.

## Files

- `candidate_summary.csv`: baseline, stress and diagnostic block summaries.
- `candidate_annual.csv`: annual frozen-candidate attribution.
- `candidate_inference.csv`: date-block uncertainty.
- `matched_candidate.csv`: full-sequence matched-time controls.
- `promotion_gates.csv`: frozen gate outcomes.
- `source_audit.csv`: annual source hashes, row counts and bounds.
- `decision.json`: machine-readable decision.
- `independent_forward_reconstruction.json`: independent audit summary.
