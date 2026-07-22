# Independent Review — DTR-NQ-WP-20260722-14

## Verdict

`INDEPENDENT_REVIEW_PASS`

## Checks completed

- Frozen 304-trade E6 stream reproduced exactly.
- Normal, two-tick-per-side and four-tick-per-side cost transformations rebuilt independently.
- All nine historical final-equity and maximum-drawdown paths reproduced.
- Current-equity compounding verified trade by trade.
- Date-block and month-block definitions verified.
- Independent 10,000-run resamples executed under different seed families.
- Risk ordering and cost ordering verified monotonic.
- Complete primary rerun reproduced nine of nine artifacts byte-identically.

## Independent conclusions

- All nine observed historical paths finished above starting capital.
- 0.50% risk was the most drawdown-resilient tested envelope.
- 1.00% risk remained historically profitable but developed meaningful 20% drawdown tail risk under severe costs.
- 1.50% risk developed materially high 20–30% drawdown risk, especially under severe costs.
- No historical result authorizes live sizing or deployment.

## Final verdict

Accept the research evidence. Close Block 6 against further historical risk tuning. Preserve 0.50% and 1.00% only as paper-research envelopes and do not treat 1.50% as a balanced default.
