# DTR Research Decision Ledger

This ledger is the durable entry point for completed DTR research decisions. Detailed reports and machine-readable evidence remain authoritative; this file records where they live, what was decided, and what must change before a rejected or held line is reopened.

## Evidence hierarchy

1. **Execution regression benchmark** — `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`
   - 495 trades; 86.004761R; 0.173747R expectancy.
   - Purpose: validate the causal execution engine and detect unintended code changes.

2. **Advanced-context research comparator** — `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`
   - 477 trades; 42.577515R; 0.089261R expectancy.
   - Purpose: fixed comparator for the timing-corrected historical context program.

3. **Frozen challengers**
   - E5: 335 trades; 49.464423R; 0.147655R expectancy.
   - E6: 304 trades; 48.937550R; 0.160979R expectancy.
   - Neither replaces the comparator until fresh-data and data-validity gates pass.

4. **Shadow, risk-watch and sizing evidence**
   - E5+E6 and E6+Monday remain shadow-only.
   - P2, P3, R2 and I1 remain historical diagnostics only.
   - FOMC-pre and expiration/roll-overlap are fixed risk-watch cohorts only.
   - 0.50% and 1.00% are paper-research risk envelopes only; 1.50% is classified as aggressive.

## DTR-NQ-WP-20260722-08 — Advanced context robustness

Decision: `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`.

Authoritative files:

- `docs/DTR_ADVANCED_CONTEXT_RESEARCH_2026-07-22.md`
- `docs/FRESH_OOS_CONTEXT_CHALLENGERS_2026-07-22.md`
- `results/2026-07-22/advanced_context_summary.json`
- `results/2026-07-22/advanced_context_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-08.md`

Reusable conclusion: E5 and E6 are coherent historical challengers, but their incremental advantage remains unresolved. Do not retune them on the same sample.

## DTR-NQ-WP-20260722-09 — Monday inclusion × Asia exclusion

Decision: `RETAIN_TUE_FRI_AND_ASIA`.

Authoritative files:

- `docs/MONDAY_ASIA_FACTORIAL_RESEARCH_2026-07-22.md`
- `results/2026-07-22/nq_monday_asia_factorial_results.csv`
- `results/2026-07-22/nq_monday_asia_factorial_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-09.md`

Reusable conclusion: adding Monday is not a stable improvement, removing Asia is harmful, and the combined arm is rejected. Reopen only on new or cross-market data.

## DTR-NQ-WP-20260722-10 — E6 advanced test framework

Decision: `FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`.

Authoritative files:

- `docs/E6_ADVANCED_TEST_FRAMEWORK_2026-07-22.md`
- `results/2026-07-22/e6_advanced_test_framework_preregistration.json`
- `handovers/DTR-NQ-WP-20260722-10.md`

Reusable conclusion: E6 is the working historical baseline, while the unfiltered comparator remains mandatory. Historical work cannot authorize Pine or deployment.

## DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space execution

Decision: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.

Authoritative files:

- `docs/E6_ADVANCED_BLOCKS_0_3_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_blocks_0_3_candidate_results.csv`
- `results/2026-07-22/e6_blocks_0_3_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-11.md`

Reusable conclusion: E6's mechanism is supported. No path or clearance rule improved the portfolio; P3 remains only a long-history/cross-market replication hypothesis. Do not retune P1–P3, R1–R2 or I1 on 2023–2025.

## DTR-NQ-WP-20260722-12 — E6 portfolio sequencing

Decision: `RETAIN_S0_GLOBAL_SEQUENCING`.

Authoritative files:

- `docs/E6_SEQUENCING_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_sequencing_results.csv`
- `results/2026-07-22/e6_sequencing_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-12.md`

Reusable conclusion: first-trade-only, 60-minute cooldown and one-third-risk session sleeves were inferior. Do not search alternate cooldowns, daily limits or sleeve weights on the current sample.

## DTR-NQ-WP-20260722-13 — E6 event, holiday and rollover attribution

Decision: `RETAIN_E6_NO_EVENT_EXCLUSION_WATCH_FOMC_PRE_AND_ROLL_EXPIRY_OVERLAP`.

Authoritative files:

- `results/2026-07-22/e6_event_roll_preregistration.json`
- `docs/E6_EVENT_ROLL_ATTRIBUTION_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_event_roll_results.csv`
- `results/2026-07-22/e6_event_roll_overlap_decomposition.csv`
- `results/2026-07-22/e6_event_roll_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-13.md`

Reusable conclusion: FOMC weakness was concentrated in nine pre-statement trades. Expiration and roll weakness came from the same 18-trade overlap. No event exclusion is authorized. Reopen only on longer, fresh or cross-market data using unchanged definitions.

## DTR-NQ-WP-20260722-14 — E6 fixed-fraction equity and execution-cost stress

Decision: `EQUITY_COST_STRESS_COMPLETE_NO_SIZING_AUTHORIZATION`.

Authoritative files:

- `results/2026-07-22/e6_equity_cost_stress_preregistration.json`
- `docs/E6_EQUITY_COST_STRESS_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_equity_cost_stress_historical.csv`
- `results/2026-07-22/e6_equity_cost_stress_bootstrap.csv`
- `results/2026-07-22/e6_equity_cost_stress_independent_review.json`
- `results/2026-07-22/e6_equity_cost_stress_deterministic_repeat.json`
- `reviews/DTR-NQ-WP-20260722-14-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-14.md`
- `changelogs/DTR-NQ-WP-20260722-14.md`

Reusable conclusion:

- All nine observed $100,000 account paths finished profitable.
- Normal-cost observed final equity was $126,940 / $159,185 / $197,231 at 0.50% / 1.00% / 1.50% risk.
- Normal-cost observed maximum drawdown was 4.3% / 8.4% / 12.4%.
- Severe-cost 1.00% risk had a resampled 95th-percentile drawdown of approximately 22.9–25.5% and a 10.6–16.6% probability of reaching 20% drawdown.
- Severe-cost 1.50% risk reached 20% drawdown in approximately 45.1–54.9% of resamples and 30% drawdown in approximately 8.5–13.7%.
- Preserve 0.50% and 1.00% only as paper-research envelopes. Do not treat 1.50% as a balanced default.
- No live sizing, leverage, Pine or deployment authorization follows.

Do not search additional risk fractions, dynamic sizing, volatility scaling, drawdown throttles, Kelly fractions or cost-dependent sizing on the 2023–2025 sample.

## Current forward decision

The bounded E6 historical programme is complete. The next valid evidence must come from qualified fresh NQ data, materially longer contract-audited NQ history, or unchanged ES replication. The repository must retain the unfiltered comparator alongside E5 and E6 until fresh evidence establishes incremental value.
