# Baseline Validity Reset — Causal and Statistical Design

## Decision problem

Determine whether the NQ reversal strategy retains a credible research edge after correcting the noncausal open-trade gap rule and after explicitly testing timestamp, rollover, concentration, and selection-pressure risks.

## 1. Gap-policy alternatives

### Historical observe-only reference

Preserve the original 504-trade engine for regression only. It may bridge missing data and is not a deployable benchmark.

### Retrospective reject policy

Preserve the existing 491-trade result for historical attribution only. It is noncausal and may not remain the benchmark.

### Causal conservative liquidation

This is the proposed benchmark policy.

At every observed one-minute bar, the engine knows the previous observed timestamp. If the interval between the previous observation and the current bar is classified as unsafe and the position was open across that interval:

1. the gap becomes known at the current bar timestamp;
2. no missing intragap path is synthesized;
3. the position is liquidated at the first post-gap observable open using a conservative price;
4. the long exit price is `min(active_stop_execution_price, current_open - slippage)`;
5. the short exit price is `max(active_stop_execution_price, current_open + slippage)`;
6. if the gap crossed a scheduled close or maximum-hold deadline, the same first-observable liquidation still applies;
7. the trade receives `GAP_LIQUIDATION` or a more specific reason code;
8. the actual liquidation timestamp controls the one-position-at-a-time sequence.

This deliberately allows losses beyond the nominal stop when the market reopens through it.

## 2. Timestamp hypothesis test

The dataset does not establish whether timestamps denote bar opens or closes. The test will compare at least:

- vendor `Vwap_ETH` against reconstructed VWAP under bar-open and one-minute-shifted bar-close interpretations;
- reset alignment around the presumed 18:00 ET ETH session boundary;
- known maintenance and Sunday-open gaps;
- consistency of one-minute to five-minute aggregation under each convention.

The result may be `BAR_OPEN_SUPPORTED`, `BAR_CLOSE_SUPPORTED`, or `UNRESOLVED`. A VWAP match alone is not treated as conclusive if price basis or reset rules remain ambiguous.

## 3. Rollover test

Because the source is a continuous contract with unknown construction:

- detect candidate roll discontinuities using unusually large close-to-open jumps, volume discontinuities, and quarterly contract-calendar windows;
- create exclusion bands of one and three sessions around candidate rolls;
- recompute aggregate and period metrics without changing strategy parameters;
- report the proportion of trades and net R near roll candidates.

This is a sensitivity test, not a substitute for verified contract metadata.

## 4. Selection-pressure and uncertainty tests

All code must be committed with fixed seeds.

Minimum outputs:

- trade bootstrap confidence interval for baseline expectancy;
- month-block bootstrap confidence interval;
- session-date block bootstrap;
- year/half-year dispersion;
- session×weekday attribution with coverage and uncertainty;
- walk-forward procedure aggregate;
- candidate-neighbourhood effective trial count diagnostics;
- deflated or multiple-testing-aware statistic where assumptions are explicit;
- no executive use of the selected-trade IID `probability_net_positive` figure.

## 5. Module rerun contract

After the corrected benchmark is frozen:

- continuation, IFVG, CISD, and entry-routing manifests are rerun without parameter or threshold changes;
- old and corrected benchmark results are compared separately;
- no module is rescued through new combinations;
- decisions may remain unchanged, weaken, or require fresh-data hold status.

## 6. Promotion language

The corrected in-sample benchmark can support continued research only. Deployment remains blocked until:

- timestamp and rollover risk are resolved or bounded;
- fresh untouched 2026 data is acquired under a preregistered gate;
- Python/Pine trade parity is demonstrated;
- live or paper-forward execution evidence exists.
