# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.4.0-research-closed`
Active work package: none
Decision state: `REJECT_CURRENT_SHORT_SIDE_HYPOTHESIS_NO_PAID_NQ_VALIDATION`

## Completed evidence

- Separate causal Stoic namespace, governance tree, runner, and frozen six-arm phase-one family.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- GBPUSD phase one rejected: all six arms negative.
- NQ and ES proxy phase one completed separately with independent reconstruction.
- Corrected the direction-restriction defect so entry direction no longer disables opposite-direction technical exits.
- Completed actual-NQ long-only validation: no candidate passed the promotion gates.
- Converted the post-hoc actual-NQ no-map short result into one frozen hypothesis.
- Qualified disjoint 2015-2021 and 2026 YTD USATECH proxy partitions before performance execution.
- Completed the unseen short-side falsification and independent reconstruction.

## Unseen short-side result

Older 2015-2021 proxy history:

- 696 short trades;
- `-86.13R` net;
- `-0.124R` expectancy;
- only 2 of 7 years positive;
- date-block interval `[-0.412R, +0.209R]`;
- negative under two-tick cost stress and delayed entries.

Forward 2026 YTD proxy check:

- 43 short trades;
- `+2.12R` net;
- `+0.049R` expectancy;
- date-block interval `[-0.672R, +0.914R]`;
- underperformed the simpler EMA-break control.

Only 4 of 12 gates passed. Both matched-time control tests failed.

## Scientific decision

`REJECT_CURRENT_SHORT_SIDE_HYPOTHESIS_NO_PAID_NQ_VALIDATION`

The post-hoc short asymmetry did not reproduce in the long unseen proxy history. The small 2026 gain is uncertain and does not demonstrate sequence-specific value. Paid actual-NQ validation is not justified for this current mechanical formulation.

The current mechanical Stoic 1-2-3 family is closed without a finalist.

## Restrictions

- No DTR or Asian Sweep result is changed.
- No Stoic direction, threshold, timeframe, session, weekday, stop, target, delay, matching-rule, or exit optimization.
- No new candidate may be selected from the same inspected artifacts.
- No proxy result may be represented as CME futures evidence.
- No Pine, sizing, deployment, alert, paper-trading, or profitability authorization.
