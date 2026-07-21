# Independent Review — DTR-NQ-WP-20260721-04

## Review stance

Assume CISD adds no value until causal state handling, portfolio sequencing, coverage, chronological behaviour, costs, uncertainty, and reproducibility demonstrate otherwise.

## Findings

### 1. Causal state contract

The first fixture version exposed ambiguous anchor expectations. Those fixtures were corrected to match the declared final-candle-open contract. A deeper review then found that a previously confirmed sequence could survive the start of a newer unconfirmed opposite-delivery sequence. The engine was corrected so only the newest sequence is active at the entry decision, and a regression fixture now covers this case.

Status: **passed after root-cause correction**.

### 2. Frozen baseline integrity

The observe variant reproduces 491 trades, 88.495783R net, 0.180236R expectancy, and 14.107858R maximum drawdown without parameter changes.

Status: **passed**.

### 3. Broad confirmation value

Sequence and last-candle confirmation each produce 309 trades and 0.144100R expectancy. Both reduce expectancy and return-to-drawdown. Recent-three and recent-six variants are weaker still.

Status: **failed incremental-value gate**.

### 4. Retest subset

The implementable retest portfolio has 75 trades and 0.256552R expectancy, with positive development, validation, and later-research expectancy. The frozen cohort has 73 trades and 0.291543R expectancy.

Status: **credible descriptive cohort**.

### 5. Portfolio efficiency and opportunity loss

Retest return-to-drawdown is 3.728646 versus 6.272801 for the baseline. The filter removes 418 baseline trades with +67.213139R combined result and enables two later trades that lose 2.041254R.

Status: **failed implementable portfolio gate**.

### 6. Statistical incremental value

Trade and month-block bootstrap intervals for retest-minus-complement expectancy include zero. The one-sided permutation p-value is 0.210289.

Status: **failed incremental-confidence gate**.

### 7. Timing stability

Entry-bar and earlier-retest subgroups reverse their relative strength across periods. The aggregate does not reveal one stable timing mechanism.

Status: **insufficient mechanism stability**.

### 8. Cost robustness

The retest portfolio remains positive through four-tick slippage, but its return-to-drawdown remains lower than baseline at every tested cost level.

Status: **absolute cost survival passed; relative gate failed**.

### 9. Reproducibility

Two clean canonical runs produced 52 of 52 byte-identical artifacts. All trade changes are attributable. Pinned Ruff and Python 3.11/3.12 CI are required on the final governance-complete head.

Status: **passed locally; final CI required before merge**.

## Decision

`REJECT_NO_INCREMENTAL_VALUE`

This permits:

- merging the causal detector, tests, manifests, negative evidence, and diagnostic retest annotation;
- advancing to the next independent entry-routing work package.

This does not permit:

- adding CISD as a hard filter;
- CISD-based position sizing;
- tuning sequence length, candle colour, session, weekday, direction, anchor distance, or retest timing on the current sample;
- combining CISD with rejected IFVG or held continuation logic;
- production deployment or Pine implementation.
