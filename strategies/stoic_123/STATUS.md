# Status — Stoic Edge 1-2-3

Date: 2026-07-24
Version: `v0.5.0-research-closed`
Active work package: none
Decision state: `REJECT_RTH_LONG_PROXY_HYPOTHESIS_NO_ACTUAL_NQ_VALIDATION`

## Completed evidence

- Separate causal Stoic namespace, governance tree, runner, and frozen six-arm phase-one family.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- Rejected GBPUSD phase one and failed to confirm proxy-derived NQ long candidates on actual NQ futures.
- Corrected entry-direction restrictions so opposite-direction technical management remains available.
- Rejected the post-hoc no-map short hypothesis on disjoint 2015-2021 and 2026 proxy data.
- Froze the post-hoc RTH long observation as a separate work package.
- Qualified previously uninspected USATECH history before RTH performance execution.
- Implemented UTC-to-New-York daylight-saving-aware entry classification, with full-session management retained.
- Completed the fresh 2012-2013 history and untouched 2014 holdout validation.
- Independently reconstructed 22 ledgers, 12 session-classification files and all 17 gates.

## RTH long result

Primary RTH EMA-break long-only:

- fresh 2012-2013: 858 trades, `-30.35R`, `-0.035R` expectancy, 106.95R drawdown;
- 2014 holdout: 522 trades, `-104.84R`, `-0.201R` expectancy, 108.76R drawdown;
- holdout date-block interval: `[-0.340R, -0.051R]`;
- negative under two-tick costs and delayed entries.

Secondary full RTH 1-2-3 long-only:

- fresh 2012-2013: 76 trades, `-13.31R`, `-0.175R` expectancy;
- 2014 holdout: 49 trades, `-11.24R`, `-0.229R` expectancy;
- underperformed EMA-break-only by `0.140R` expectancy on fresh history and `0.029R` on holdout.

The EMA-break-plus-retest diagnostic was also negative in both partitions. Both matched-time candidate tests failed. Only two of seventeen gates passed, both being sample-size gates.

## Scientific decision

`REJECT_RTH_LONG_PROXY_HYPOTHESIS_NO_ACTUAL_NQ_VALIDATION`

RTH filtering reduced full-sequence losses relative to broader entry sets but did not produce positive expectancy. The earlier positive RTH attribution did not transfer to fresh proxy history. Additional actual-NQ validation is not justified for this formulation.

The current mechanical Stoic 1-2-3 family remains closed without a finalist.

## Restrictions

- No DTR or Asian Sweep result is changed.
- No Stoic direction, threshold, timeframe, session subdivision, weekday, volatility, stop, target, delay, matching-rule or exit optimization.
- No new candidate may be selected from the inspected artifacts.
- No proxy result may be represented as CME futures evidence.
- No Pine, sizing, deployment, alert, paper-trading or profitability authorization.
