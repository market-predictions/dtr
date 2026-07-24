# Active Claim

- Work package: `AS-WP-20260723-09`
- Branch: `agent/asia-sweep-pdh-pdl-cluster-final`
- Claimed scope: final London PDH/PDL–Asian-boundary liquidity-cluster challenger
- Started: 2026-07-23
- Input boundary: corrected Auction-State diagnostic merge `bd73b340c5f1124d4910ae44aee32d7b9d1fddb2`
- Data boundary: private Dukascopy NQ/ES BID proxies; development outcomes through 2024-06-30 only
- Frozen cluster distance: 10% of Asian-range width
- Frozen Asian-range regime: causal 20th–80th percentile of preceding 60 valid ranges
- Frozen execution: impulse-break entry, two-tick sweep-extreme stop, Asian midpoint target, 06:00 time exit, realistic fixed costs
- Constraint: no threshold search, validation access, weekday/direction/instrument selection, DTR combination, Pine or deployment work
- Status: exact-head private development replay triggered after checksum-verified clean installation
