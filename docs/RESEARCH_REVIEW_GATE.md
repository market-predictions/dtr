# DTR Research Review Gate

This gate is applied independently from candidate construction before a model or module can be promoted.

## Reviewer stance

The reviewer assumes the apparent edge is false until the evidence survives attempts to disprove it. Candidate generation and candidate review are treated as separate roles, even when performed in the same development environment.

## Gate A — Reproducibility

- [ ] The run is defined by a versioned manifest.
- [ ] Dataset, manifest, and code commit hashes are recorded.
- [ ] One clean rerun reproduces trade count, trade timestamps, exit reasons, net R, and drawdown within declared tolerances.
- [ ] Generated reports are derived from the trade log rather than manually edited.
- [ ] Randomized analyses record and reuse their seeds.

## Gate B — Data integrity

- [ ] Incomplete source dates are excluded.
- [ ] Maintenance, weekend, holiday, and unexplained gaps are classified.
- [ ] Probable contract-roll discontinuities are identified.
- [ ] Trades cannot bridge unexplained gaps or unsafe roll transitions.
- [ ] Timestamp, timezone, daylight-saving, and session-boundary assumptions are documented and tested.
- [ ] Supplied VWAP fields are treated as comparison targets until independently reconstructed.

## Gate C — Causal contribution

- [ ] The candidate is compared with the frozen baseline.
- [ ] Every new module is tested alone before combination.
- [ ] Opportunity coverage and rejected setups are reported.
- [ ] Redundant filters are identified through ablation.
- [ ] Entry and exit changes are not optimized simultaneously in the first pass.
- [ ] The result does not depend on one symbol, session, weekday, direction, or month without explicit justification.

## Gate D — Overfitting resistance

- [ ] Candidate selection occurs inside the training window.
- [ ] Validation and forward windows do not influence parameter selection.
- [ ] Neighbouring parameter values remain viable.
- [ ] The candidate survives session-removal, weekday-removal, and regime-removal stress.
- [ ] Walk-forward folds are reported individually, including weak and losing folds.
- [ ] The ranking penalizes small samples and parameter cliffs.

## Gate E — Execution realism

- [ ] Commission and slippage are nonzero.
- [ ] Results survive stressed transaction costs.
- [ ] Same-minute stop/target ambiguity uses a conservative policy or is reported separately.
- [ ] Futures quantities are whole contracts in production simulations.
- [ ] Minimum-contract risk is checked against the intended risk budget.
- [ ] Daily close and maximum-hold logic consume stale setup state.

## Gate F — Statistical interpretation

- [ ] Expectancy, median R, profit factor, drawdown, MFE, MAE, and holding time are reported.
- [ ] Confidence or bootstrap uncertainty is reported.
- [ ] Monte Carlo conclusions are not presented as protection against structural regime failure.
- [ ] A positive aggregate result is not promoted when most chronological folds are weak or negative.
- [ ] The report distinguishes exploratory, validation, forward, and live-paper evidence.

## Gate G — Promotion decision

A candidate can be promoted only when:

1. reproducibility and data-integrity gates pass;
2. it adds independent value versus the baseline;
3. it remains viable under costs and neighbouring parameters;
4. walk-forward evidence is acceptable;
5. known limitations are explicit;
6. the reviewer records one of:
   - `PROMOTE_TO_NEXT_RESEARCH_PHASE`
   - `HOLD_FOR_MORE_DATA`
   - `REJECT_OVERFIT`
   - `REJECT_NO_INCREMENTAL_VALUE`
   - `REJECT_DATA_OR_EXECUTION_RISK`

## Current candidate status

`DTR_PY_NQ_CANDIDATE_0_1`: **HOLD_FOR_MORE_DATA**

Reason: promising reversal evidence, but manifest rerun, timestamp/rollover integrity, continuation comparison, and genuinely unseen post-December-2025 data are still outstanding.
