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

4. **Current NQ working baseline**
   - `E6_NO_FOMC_DAY`: 291 trades; 53.483342R; 0.183792R expectancy; 9.151061R maximum drawdown.
   - Classification: user-mandated risk-policy overlay, not statistically proven promotion.

5. **Sizing evidence**
   - 0.50% and 1.00% remain paper-research envelopes only.
   - 1.50% remains classified as aggressive.

6. **Cross-market evidence**
   - Dukascopy USA500 is a bid-CFD S&P 500 proxy, not ES futures.
   - Initial E6 proxy result: 281 trades; 13.330895R; 0.047441R expectancy.
   - Classification: `PARTIAL_COST_FRAGILE_REPLICATION`.

## DTR-NQ-WP-20260722-08 — Advanced context robustness

Decision: `NO_HISTORICAL_PROMOTION_CONTINUE_FRESH_OOS_RESEARCH`.

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

Authoritative files include `docs/E6_NO_FOMC_BASELINE_DECISION_2026-07-22.md`, `results/2026-07-22/e6_no_fomc_baseline.json`, and `handovers/DTR-NQ-WP-20260722-15.md`.

Conclusion:

- The user explicitly selected no entries on official FOMC statement dates as a risk-policy baseline rule.
- Exact portfolio resequencing produced 291 trades, 53.483342R, 0.183792R expectancy, and 9.151061R maximum drawdown.
- Original E6 remains the frozen comparator.

## DTR-NQ-WP-20260722-16 — No-FOMC risk recalibration

Decision: `NO_FOMC_RISK_RECALIBRATION_COMPLETE_NO_SIZING_AUTHORIZATION`.

Conclusion:

- Normal-cost final equity at 0.50% / 1.00% / 1.50% risk: $129,885 / $166,725 / $211,540.
- Normal-cost maximum drawdown: 4.51% / 8.87% / 13.09%.
- Severe-cost 1.00% risk retained approximately 7.1–10.1% probability of reaching 20% drawdown.
- Severe-cost 1.50% risk retained approximately 36.6–42.9% probability of reaching 20% drawdown and 5.6–8.2% probability of reaching 30% drawdown.
- No live sizing, leverage, Pine, or deployment authorization follows.

## DTR-ESPROXY-WP-20260722-17 — USA500 data acquisition and qualification

Decision: `QUALIFIED_WITH_PROXY_LIMITATIONS`.

Authoritative files:

- `docs/USA500_DUKASCOPY_PROXY_QUALIFICATION_2026-07-22.md`
- `results/2026-07-22/usa500_dukascopy_proxy_qualification.json`
- `handovers/DTR-ESPROXY-WP-20260722-17.md`

Conclusion:

- 1,348,078 active one-minute bid candles were retained after removing synthetic zero-volume placeholders.
- Timestamps, ordering, OHLC integrity and frozen session coverage passed.
- The data is a Dukascopy CFD proxy and cannot validate CME ES prices, volume, spread or roll behavior.
- Raw data remains outside Git and must be deleted after research use.

## DTR-CROSSMARKET-WP-20260722-18 — NQ versus USA500 parallel replication

Decision: `PARTIAL_COST_FRAGILE_REPLICATION`.

Authoritative files:

- `results/2026-07-22/nq_usa500_parallel_preregistration.json`
- `src/dtr_lab/research/cross_market.py`
- `scripts/run_nq_usa500_parallel.py`
- `docs/NQ_USA500_PARALLEL_REPLICATION_2026-07-22.md`
- `results/2026-07-22/nq_usa500_parallel_summary.csv`
- `results/2026-07-22/nq_usa500_parallel_inference.csv`
- `results/2026-07-22/nq_usa500_parallel_session_breakdown.csv`
- `results/2026-07-22/nq_usa500_parallel_independent_review.json`
- `results/2026-07-22/nq_usa500_parallel_deterministic_repeat.json`
- `handovers/DTR-CROSSMARKET-WP-20260722-18.md`

Conclusion:

- The parallel framework reproduced NQ E6 and NQ E6 no-FOMC exactly.
- USA500 E6 produced 281 trades, +13.330895R, 0.047441R expectancy and 17.377216R maximum drawdown.
- USA500 E6 expectancy became -0.011853R at two ticks per side.
- The date-block 95% proxy expectancy interval crossed zero broadly.
- Proxy performance was concentrated in London: +31.13R, versus -7.23R in Asia and -10.57R in New York.
- The no-FOMC overlay improved NQ by +4.55R but reduced proxy total return by 0.35R after resequencing.
- Do not create a London-only proxy rule, modify E6, pool instruments, or claim ES futures validation.

## Current forward decision

The initial provider-neutral cross-market framework is complete. Valid next evidence is:

- materially longer USA500 proxy history with no framework changes;
- actual contract-audited ES futures data;
- qualified fresh post-2025 NQ data; or
- materially longer contract-audited NQ history.

Do not tune the proxy to rescue the weak or cost-fragile result.
