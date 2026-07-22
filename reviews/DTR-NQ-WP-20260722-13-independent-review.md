# Independent Review — DTR-NQ-WP-20260722-13

## Verdict

`INDEPENDENT_REVIEW_PASS`

## Checks completed

- Registered raw archive checksum matched.
- Frozen 304-trade E6 stream reproduced exactly.
- FOMC, CPI and NFP date and release-time masks rebuilt independently.
- Expiration-week and roll-window masks rebuilt from the frozen official dates and observed ETH market dates.
- All category metrics, cost stresses and classifications reproduced.
- Roll-window maintenance gaps and percentiles reproduced.
- Primary event-label matrix matched the independent reconstruction for every trade.
- Date-block uncertainty rerun under a different fixed seed.
- Deterministic repeat evidence matched.

## Key audit conclusions

- FOMC-day weakness is concentrated in the nine pre-statement entries; the five post-statement entries were positive.
- Expiration-week and roll-window weakness is concentrated in their shared 18-trade cohort. Expiration-only and roll-only cohorts were positive.
- No roll-date trades occurred because official roll dates are Mondays and frozen E6 trades Tuesday–Friday.
- No official roll window exceeded the frozen 99th-percentile maintenance-gap threshold.
- No category can be converted into a historical exclusion under the preregistration.

## Final conclusion

Retain E6 unchanged. Preserve FOMC-pre and expiration/roll-overlap as fixed risk-watch cohorts for longer or fresh data. Proceed to the already authorized fixed-fraction equity and cost-stress block.
