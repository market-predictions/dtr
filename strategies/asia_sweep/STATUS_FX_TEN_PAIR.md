# Asian Sweep Ten-Pair FX Status

Date: 2026-07-25  
Work package: `AS-WP-20260725-10`  
State: `DISCOVERY_RUN_PENDING_PNL_BLOCKED`

## Current question

Does a causally confirmed London rejection of the completed Asian range add positive 60-minute reversal value relative to matched non-rejection boundary breaches across ten FX pairs?

## Fixed discovery scope

- universe: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP;
- period: 2015–2019 only;
- signal: synchronized active midpoint OHLC;
- primary event: London `REJECTION` from the unchanged auction-state detector;
- controls: five distinct-date non-rejection boundary events matched within pair/year/weekday/30-minute bucket;
- endpoint: reversal-signed 60-minute midpoint return divided by Asian-range width;
- inference: calendar-date block bootstrap and clustered sign permutation.

## Blocked

- 2020 onward outcome inspection;
- executable entries, stops, targets, costs and strategy P&L;
- pair/session/direction/weekday/range-regime selection;
- PDH/PDL cluster rescue;
- Pine and deployment.

## Next state transition

- pass: authorize unchanged 2020–2021 mechanism validation;
- fail: stop this formulation before execution research.
