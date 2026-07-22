# Independent Review — DTR-NQ-WP-20260722-08

## Verdict

`ACCEPT_RESEARCH_EVIDENCE_NO_PROMOTION`

The advanced context study is reproducible, causal at the feature boundary and honest about selection pressure. The correct decision is to retain two single-factor challengers for fresh out-of-sample comparison while refusing historical promotion.

## Verified

- 477-trade, 42.577515R baseline reconstructed exactly.
- 492 pre-overlap signals and 1,666 eligible sessions.
- zero D1, H4, weekly or range-completion causality violations.
- 37 univariate categories, six broad exclusions and six capped interactions evaluated.
- every reported portfolio metric independently recalculated from trade CSVs.
- all primary outputs reproduced byte-for-byte.
- threshold sensitivity reported as a surface rather than used to select a new optimum.

## Strongest evidence

The compressed-range and prior-day-proximity exclusions both:

- retain more than 300 trades at the frozen threshold;
- improve historical expectancy and drawdown materially;
- remain positive in all three years;
- remain positive at two ticks each side;
- remain directionally favorable under nearby fixed threshold perturbations.

## Material limitations

- The 42.58R baseline was itself chosen after timing sensitivity inspection.
- Paired bootstrap intervals for incremental net R include zero.
- The strongest interaction retains only 220 trades and fails the frozen sample gate.
- The prior-day finding runs opposite the original liquidity-level hypothesis and may be partly definition-specific.
- Directional filters are inconsistent across D1, H4 and confluence states.
- Contract construction and fresh timestamp metadata remain external data requirements.

## Required next action

Run Arm 0, Arm A and Arm B on qualified untouched data under the committed supplementary preregistration. Keep the combined rule shadow-only.
