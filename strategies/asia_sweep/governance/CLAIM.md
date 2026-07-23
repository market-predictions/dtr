# Active Claim

- Work package: `AS-WP-20260723-09`
- Branch: `agent/asia-sweep-pdh-pdl-cluster-challenger`
- Claimed scope: final London PDH/PDL–Asian-boundary liquidity-cluster challenger
- Started: 2026-07-23
- Input boundary: corrected Auction-State diagnostic closure head `a7738ed2e5b2c915ef8bf03b57352c387b5ddea7`
- Data boundary: private Dukascopy NQ/ES BID proxies; development outcomes through 2024-06-30 only
- Frozen cluster distance: 10% of Asian-range width
- Frozen Asian-range regime: causal 20th–80th percentile of preceding 60 valid ranges
- Frozen execution: impulse-break entry, two-tick sweep-extreme stop, Asian midpoint target, 06:00 time exit, realistic fixed costs
- Constraint: no threshold search, validation access, weekday/direction/instrument selection, DTR combination, Pine or deployment work
- Status: implementation and protected development replay in progress
