# DTR Research Decision Ledger

This ledger is the durable entry point for completed DTR research decisions. Detailed reports and machine-readable evidence remain authoritative; this file records where they live, what was decided, and what must change before a rejected or held line is reopened.

## Evidence hierarchy

1. **Execution regression benchmark** — `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`
   - 495 trades; 86.004761R; 0.173747R expectancy.
   - Purpose: validate the causal execution engine and detect unintended code changes.
   - It is not a deployable strategy authorization.

2. **Advanced-context research comparator** — `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`
   - 477 trades; 42.577515R; 0.089261R expectancy.
   - Purpose: fixed comparator for the timing-corrected historical context program.
   - It was selected after timing sensitivity inspection and remains exploratory.

3. **Frozen challengers**
   - E5: `E5_EXCLUDE_COMPRESSED_RANGE` — 335 trades; 49.464423R; 0.147655R expectancy.
   - E6: `E6_EXCLUDE_NEAR_PRIOR_DAY_DIRECTIONAL_EXTREME` — 304 trades; 48.937550R; 0.160979R expectancy.
   - Purpose: unchanged fresh-OOS challengers. Neither replaces the comparator until it passes fresh-data and data-validity gates.

4. **Shadow-only challengers**
   - E5+E6 interaction — 220 historical trades; under the frozen 250-trade historical gate.
   - E6+Monday — historical coverage diagnostic only; lower expectancy and drawdown efficiency than E6 A0.
   - P2 BOS quality and P3 entry-extension rules — historical E6 diagnostics only; neither improved portfolio-level E6 performance.
   - R2 runner clearance and I1 BOS-quality/TP1-clearance interaction — predeclared low-sample shadows only.

## DTR-NQ-WP-20260722-08 — Advanced context robustness

Decision: `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`.

Authoritative files:

- `docs/DTR_ADVANCED_CONTEXT_RESEARCH_2026-07-22.md`
- `docs/FRESH_OOS_CONTEXT_CHALLENGERS_2026-07-22.md`
- `results/2026-07-22/advanced_context_summary.json`
- `results/2026-07-22/advanced_context_independent_review.json`
- `handovers/DTR-NQ-WP-20260722-08.md`

Reusable conclusion:

- E5 and E6 are coherent historical challengers.
- Their historical paired incremental advantage versus the unfiltered comparator remains unresolved.
- No additional threshold search, context-family expansion, or historical promotion is permitted on the same sample.

Reopen only when at least one of the following changes:

- qualified untouched post-2025 NQ data becomes available;
- a materially longer, contract-audited NQ history is acquired;
- unchanged cross-market replication data, such as ES, is available;
- timestamp or continuous-contract methodology is authoritatively resolved.

## DTR-NQ-WP-20260722-09 — Monday inclusion × Asia exclusion

Decision: `RETAIN_TUE_FRI_AND_ASIA`.

Authoritative files:

- `docs/MONDAY_ASIA_FACTORIAL_RESEARCH_2026-07-22.md`
- `results/2026-07-22/nq_monday_asia_factorial_preregistration.json`
- `results/2026-07-22/nq_monday_asia_factorial_results.csv`
- `results/2026-07-22/nq_monday_asia_factorial_interaction.csv`
- `results/2026-07-22/nq_monday_asia_factorial_paired_bootstrap.csv`
- `results/2026-07-22/nq_monday_asia_factorial_independent_review.json`
- `reviews/DTR-NQ-WP-20260722-09-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-09.md`

Reusable conclusion:

- Adding Monday is not a stable broad improvement.
- Removing Asia reduces net performance under the unfiltered, E5 and E6 layers.
- The positive E6 Monday extension is dominated by Monday Asia and does not support replacing Asia.
- The combined Monday/no-Asia arm is rejected.

Do not rerun this factorial merely to reconsider the same hypothesis. Reopen only with new data, corrected execution semantics, or a separately preregistered cross-market/long-history replication.

## DTR-NQ-WP-20260722-10 — E6 advanced test framework

Decision: `FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`.

Authoritative files:

- `docs/E6_ADVANCED_TEST_FRAMEWORK_2026-07-22.md`
- `results/2026-07-22/e6_advanced_test_framework_preregistration.json`
- `workpackages/DTR-NQ-WP-20260722-10.md`
- `handovers/DTR-NQ-WP-20260722-10.md`

Reusable framework decision:

- E6 is the working baseline for the bounded historical research programme.
- The 477-trade unfiltered timing-corrected comparator remains a mandatory non-selectable control.
- Historical evidence can nominate a fresh-OOS challenger but cannot replace E6 or authorize Pine.

## DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space execution

Decision: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.

Authoritative files:

- `results/2026-07-22/e6_blocks_0_3_execution_preregistration.json`
- `docs/E6_ADVANCED_BLOCKS_0_3_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_blocks_0_3_candidate_results.csv`
- `results/2026-07-22/e6_blocks_0_3_candidate_inference.csv`
- `results/2026-07-22/e6_blocks_0_3_independent_review.json`
- `results/2026-07-22/e6_blocks_0_3_deterministic_repeat.json`
- `reviews/DTR-NQ-WP-20260722-11-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-11.md`

Reusable conclusion:

- E6's mechanism is `SUPPORTED`: near-prior-day-extreme setups had materially worse expectancy and path outcomes.
- P1 and R1 are rejected.
- P2 and P3 remain shadow-only; P3 is the only secondary long-history/cross-market replication hypothesis.
- R2 and I1 remain predeclared low-sample shadow diagnostics only.
- No rule qualified as `FRESH_OOS_CHALLENGER`.

Do not rerun or retune P1–P3, R1–R2 or I1 on the 2023–2025 NQ sample.

## DTR-NQ-WP-20260722-12 — E6 portfolio sequencing

Decision: `RETAIN_S0_GLOBAL_SEQUENCING`.

Authoritative files:

- `docs/E6_SEQUENCING_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_sequencing_preregistration.json`
- `results/2026-07-22/e6_sequencing_results.csv`
- `results/2026-07-22/e6_sequencing_inference.csv`
- `results/2026-07-22/e6_sequencing_changed_trades.csv`
- `results/2026-07-22/e6_sequencing_concurrency.json`
- `results/2026-07-22/e6_sequencing_independent_review.json`
- `results/2026-07-22/e6_sequencing_deterministic_repeat.json`
- `reviews/DTR-NQ-WP-20260722-12-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-12.md`

Reusable conclusion:

- S1 first-trade-per-ETH-date removed 45 trades that earned 7.20R and did not improve expectancy.
- S2 60-minute cooldown removed four trades that earned 1.20R and did not reduce drawdown.
- S3 session sleeves added only six trades, those trades lost 2.19R, and fixed one-third sizing materially underused risk because overlap was rare.
- All alternatives had negative observed incremental risk-normalized net R versus S0.
- Independent review and deterministic repeat passed.

Do not search alternative cooldowns, daily trade limits, sleeve weights or dynamic reallocation on the 2023–2025 sample. Reopen sequencing only with new data or a separately preregistered portfolio architecture based on an external operational requirement.

## Current forward decision

The primary fresh-data evidence remains:

- Arm 0: unfiltered timing-corrected comparator.
- Arm A: E5 compressed-range exclusion.
- Arm B: E6 prior-day-extreme exclusion.
- Arm C: E5+E6 shadow only.

While fresh data is unavailable, the next authorized historical work is diagnostic Block 5 event, holiday and rollover attribution. It may explain risk concentration but cannot create an exclusion rule from the current sample.

The repository must retain the unfiltered comparator alongside E5 and E6 until fresh data establishes whether either challenger adds genuine incremental value.
