# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.3.0-research-complete`
Active work package: none
Decision state: `NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

## Completed evidence

- Separate causal Stoic namespace, governance tree, runner, and frozen six-arm phase-one family.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- GBPUSD phase one rejected: all six arms negative.
- NQ and ES proxy phase one completed separately with independent ledger reconstruction.
- The flawed informal long-only counterfactual was corrected so entry direction no longer disables opposite-direction technical exits.
- All 18 corrected proxy/FX ledgers passed independent review.
- The preregistered actual-NQ long-only mechanism validation completed on the exact checksum-qualified archive.
- Workflow run `30036385787` passed Ruff, focused tests, checksum and source-bound preflight, full study execution, matched-control veto, raw-data removal, and artifact upload.
- Full repository CI also passed on the final validation implementation.

## Actual NQ long-only result

- No-map: 555 trades, +75.71R, +0.136R expectancy; negative in 2023; 4/9 numerical gates.
- EMA map: 252 trades, -1.83R, -0.007R expectancy; 2/9 gates.
- Strict close: 226 trades, +10.97R, +0.049R expectancy; negative in 2024; 4/9 gates.
- EMA plus breakout: 147 trades, +41.56R, +0.283R expectancy; -40.72R in 2023; 5/9 gates.
- Every 95% date-block interval crossed zero.
- No arm passed all numerical gates.
- All four arms were vetoed by the frozen matched-control contract.

## Scientific decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

The actual NQ archive does not confirm the proxy-derived EMA-map long-only thesis. Strict close does not add meaningful expectancy over a simple EMA break. EMA plus breakout remains historically interesting but chronologically unstable and statistically uncertain.

The strong historical no-map short-side result is post-hoc and may only be retained as a hypothesis for qualified unseen or materially longer contract-audited data. It does not authorize another same-sample search.

## Restrictions

- No DTR baseline or DTR result is changed.
- No Stoic threshold, timeframe, session, stop, target, delay, or exit optimization.
- No pooled instrument result.
- No Pine, sizing, deployment, alert, paper-trading, or profitability authorization.
