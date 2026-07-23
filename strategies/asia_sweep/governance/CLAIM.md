# Active Claim

- Work package: `AS-WP-20260723-08`
- Branch: `agent/asia-sweep-auction-state-diagnostic`
- Claimed scope: development-only session-specific auction-state diagnostic
- Started: 2026-07-23
- Input boundary: failed AS-A through AS-D baseline merge `c739b4fe67c3d96edf9507d5999d1c18aec39291`
- Data boundary: private Dukascopy NQ/ES BID proxies; outcomes through 2024-06-30 only
- State boundary: acceptance, rejection, two-sided and unresolved labels frozen in the work package
- Mechanism boundary: external-liquidity rejection and compressed-range acceptance only
- Output boundary: fixed-horizon signed returns, MFE/MAE and hit rates; no strategy P&L
- Constraint: no lockbox access, parameter optimization, weekday/direction/instrument selection, DTR combination, Pine or deployment work
- Status: diagnostic implementation and protected workflow in progress
