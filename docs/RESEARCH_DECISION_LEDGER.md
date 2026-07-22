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

## Current forward decision

The primary next evidence is unchanged fresh out-of-sample comparison:

- Arm 0: unfiltered timing-corrected comparator.
- Arm A: E5 compressed-range exclusion.
- Arm B: E6 prior-day-extreme exclusion.
- Arm C: E5+E6 shadow only.

The repository must retain the unfiltered comparator alongside E5 and E6 until fresh data establishes whether either challenger adds genuine incremental value.