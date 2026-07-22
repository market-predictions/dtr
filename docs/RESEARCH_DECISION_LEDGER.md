# DTR Research Decision Ledger

This ledger is the durable entry point for completed DTR research decisions. Detailed reports and machine-readable evidence remain authoritative.

## Evidence hierarchy

1. **Execution regression benchmark** — `DTR_PY_NQ_CANDIDATE_0_1_CAUSAL_GAP`
   - 495 trades; 86.004761R; 0.173747R expectancy.

2. **Timing-corrected comparator** — `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1`
   - 477 trades; 42.577515R; 0.089261R expectancy.

3. **Frozen historical challengers and controls**
   - E5: 335 trades; 49.464423R; 0.147655R expectancy.
   - Original E6: 304 trades; 48.937550R; 0.160979R expectancy.
   - Original E6 remains the mandatory control for the user-mandated no-FOMC overlay.

4. **Current working baseline**
   - `E6_NO_FOMC_DAY`: 291 trades; 53.483342R; 0.183792R expectancy; 9.151061R maximum drawdown.
   - Classification: user-mandated risk-policy overlay, not statistically proven promotion.

5. **Sizing evidence**
   - 0.50% and 1.00% remain paper-research envelopes only.
   - 1.50% remains classified as aggressive.

## DTR-NQ-WP-20260722-08 — Advanced context robustness

Decision: `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`.

Authoritative files include `docs/DTR_ADVANCED_CONTEXT_RESEARCH_2026-07-22.md` and `handovers/DTR-NQ-WP-20260722-08.md`.

Conclusion: E5 and E6 are coherent historical challengers, but their incremental advantage remains unresolved. Do not retune them on the same sample.

## DTR-NQ-WP-20260722-09 — Monday inclusion × Asia exclusion

Decision: `RETAIN_TUE_FRI_AND_ASIA`.

Conclusion: adding Monday is not a stable improvement, removing Asia is harmful, and the combined arm is rejected.

## DTR-NQ-WP-20260722-10 — E6 advanced test framework

Decision: `FRAMEWORK_FROZEN_EXECUTION_NOT_STARTED`.

Conclusion: E6 is the working historical baseline for bounded tests while the unfiltered comparator remains mandatory. Historical work cannot authorize Pine or deployment.

## DTR-NQ-WP-20260722-11 — E6 mechanism, path and reward-space

Decision: `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.

Conclusion: E6's mechanism is supported. No path or clearance rule improved the portfolio. Do not retune P1–P3, R1–R2, or I1 on 2023–2025.

## DTR-NQ-WP-20260722-12 — E6 portfolio sequencing

Decision: `RETAIN_S0_GLOBAL_SEQUENCING`.

Conclusion: first-trade-only, cooldown, and fixed session sleeves were inferior. Do not search alternate cooldowns, daily limits, or sleeve weights.

## DTR-NQ-WP-20260722-13 — Event, holiday, and rollover attribution

Decision: `RETAIN_E6_NO_EVENT_EXCLUSION_WATCH_FOMC_PRE_AND_ROLL_EXPIRY_OVERLAP`.

Conclusion: FOMC weakness was concentrated in nine pre-statement trades. Expiration and roll weakness came from the same 18-trade overlap. The study itself did not statistically authorize an event exclusion.

## DTR-NQ-WP-20260722-14 — Original E6 equity and cost stress

Decision: `EQUITY_COST_STRESS_COMPLETE_NO_SIZING_AUTHORIZATION`.

Conclusion:

- Normal-cost final equity at 0.50% / 1.00% / 1.50% risk: $126,940 / $159,185 / $197,231.
- Normal-cost maximum drawdown: 4.3% / 8.4% / 12.4%.
- Severe-cost 1.50% risk produced materially high 20–30% drawdown tail risk.
- No live sizing authorization.

## DTR-NQ-WP-20260722-15 — E6 no-FOMC working baseline

Decision: `PROMOTE_E6_NO_FOMC_DAY_AS_WORKING_BASELINE`.

Authoritative files:

- `docs/E6_NO_FOMC_BASELINE_DECISION_2026-07-22.md`
- `results/2026-07-22/e6_no_fomc_baseline.json`
- `handovers/DTR-NQ-WP-20260722-15.md`
- `changelogs/DTR-NQ-WP-20260722-15.md`

Conclusion:

- The user explicitly selected no entries on official FOMC statement dates as a risk-policy baseline rule.
- Exact portfolio resequencing produced 291 trades, 53.483342R, 0.183792R expectancy, and 9.151061R maximum drawdown.
- Original E6 remains the frozen comparator.

## DTR-NQ-WP-20260722-16 — No-FOMC risk recalibration

Decision: `NO_FOMC_RISK_RECALIBRATION_COMPLETE_NO_SIZING_AUTHORIZATION`.

Authoritative files:

- `docs/E6_NO_FOMC_RISK_RECALIBRATION_RESEARCH_2026-07-22.md`
- `results/2026-07-22/e6_no_fomc_risk_recalibration_preregistration.json`
- `results/2026-07-22/e6_no_fomc_risk_recalibration_historical.csv`
- `results/2026-07-22/e6_no_fomc_risk_recalibration_summary.json`
- `reviews/DTR-NQ-WP-20260722-16-independent-review.md`
- `handovers/DTR-NQ-WP-20260722-16.md`
- `changelogs/DTR-NQ-WP-20260722-16.md`

Conclusion:

- Normal-cost final equity at 0.50% / 1.00% / 1.50% risk: $129,885 / $166,725 / $211,540.
- Normal-cost maximum drawdown: 4.51% / 8.87% / 13.09%.
- Severe-cost 1.00% risk retained approximately 7.1–10.1% probability of reaching 20% drawdown.
- Severe-cost 1.50% risk retained approximately 36.6–42.9% probability of reaching 20% drawdown and 5.6–8.2% probability of reaching 30% drawdown.
- The no-FOMC policy improves growth and severe-cost resilience, but does not change the risk hierarchy.
- No live sizing, leverage, Pine, or deployment authorization follows.

## Current forward decision

The next valid work is data acquisition and qualification rather than further NQ in-sample tuning:

- qualified fresh NQ data;
- materially longer contract-audited NQ history; or
- Dukascopy `USA500.IDX/USD` as a separately labelled S&P 500 CFD proxy.

The Dukascopy proxy must pass history, session, timestamp, missing-bar, spread, and discontinuity audits before any performance result is inspected. It must not be described as exchange-traded ES futures data, and original E6 must remain a control beside the no-FOMC baseline.
