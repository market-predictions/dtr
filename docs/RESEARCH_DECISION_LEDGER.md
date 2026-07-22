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

Frozen four-arm design:

- A0: Tuesday–Friday; Asia, London and New York.
- A1: Monday–Friday; Asia, London and New York.
- A2: Tuesday–Friday; London and New York.
- A3: Monday–Friday; London and New York.

Reusable conclusion:

- Adding Monday is not a stable broad improvement.
- Removing Asia reduces net performance under the unfiltered, E5 and E6 layers.
- The positive E6 Monday extension is dominated by Monday Asia and does not support replacing Asia.
- The combined Monday/no-Asia arm is rejected.
- No Pine, sizing, execution or primary OOS-arm change follows from this study.

Do not rerun this factorial merely to reconsider the same hypothesis. Reopen only with new data, corrected execution semantics, or a separately preregistered cross-market/long-history replication. Do not change thresholds after seeing the existing result.

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
- Authorized selectable families are P1–P3 path quality, R1–R2 reward space and S1–S3 sequencing.
- The only authorized interaction is P2 + R1 and it is shadow-only.
- Mechanism, event/roll and fixed-fraction risk blocks are diagnostic and cannot create filters from descriptive buckets.
- Historical evidence can nominate a fresh-OOS challenger but cannot replace E6 or authorize Pine.

Do not alter E6's 0.25 D1-ATR threshold, search neighboring thresholds, reopen weekday/session selection or add interactions after results. Any extension requires a new preregistration and a separate work package.

## DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space execution

Decision: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.

Authoritative files:

- `results/2026-07-22/e6_blocks_0_3_execution_preregistration.json`
- `docs/E6_ADVANCED_BLOCKS_0_3_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_blocks_0_3_mechanism_decision.json`
- `results/2026-07-22/e6_blocks_0_3_mechanism_summary.csv`
- `results/2026-07-22/e6_blocks_0_3_mechanism_strata.csv`
- `results/2026-07-22/e6_blocks_0_3_candidate_results.csv`
- `results/2026-07-22/e6_blocks_0_3_candidate_inference.csv`
- `results/2026-07-22/e6_blocks_0_3_changed_trade_attribution.csv`
- `results/2026-07-22/e6_blocks_0_3_independent_bootstrap.csv`
- `results/2026-07-22/e6_blocks_0_3_independent_review.json`
- `results/2026-07-22/e6_blocks_0_3_deterministic_repeat.json`
- `reviews/DTR-NQ-WP-20260722-11-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-11.md`

Reusable conclusion:

- E6's mechanism is `SUPPORTED`: near-prior-day-extreme setups had 0.224414R lower expectancy, a 7.1-point higher stop-first rate, lower MFE and lower TP1/TP2 hit rates.
- The kept cohort had higher expectancy in all three tested years and all three sessions.
- P1 and R1 are rejected.
- P2 and P3 remain shadow-only; P3 is the only secondary long-history/cross-market replication hypothesis.
- R2 and I1 remain predeclared low-sample shadow diagnostics only.
- Every candidate produced less total return than E6 after portfolio resequencing; all paired intervals crossed zero and no rule qualified as `FRESH_OOS_CHALLENGER`.
- Blocks 0–3 reproduced deterministically and passed independent review.

Do not rerun or retune P1–P3, R1–R2 or I1 on the 2023–2025 NQ sample. Reopen P3 only with new, materially longer or cross-market data using the frozen 0.35R rule.

## Current forward decision

The primary fresh-data evidence remains:

- Arm 0: unfiltered timing-corrected comparator.
- Arm A: E5 compressed-range exclusion.
- Arm B: E6 prior-day-extreme exclusion.
- Arm C: E5+E6 shadow only.

While fresh data is unavailable, the next authorized historical work is the separately frozen E6 sequencing family:

- S0 current global sequencing;
- S1 first trade per ETH market date;
- S2 60-minute post-exit cooldown;
- S3 risk-normalized Asia, London and New York session sleeves.

The repository must retain the unfiltered comparator alongside E5 and E6 until fresh data establishes whether either challenger adds genuine incremental value.
