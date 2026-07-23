# Active Claim

- Work package: `AS-WP-20260723-06`
- Branch: `agent/asia-sweep-proxy-normalization-contract`
- Claimed scope: synthetic proxy event/bar normalization from 0.001 source quotes to the frozen instrument-specific execution grid
- Started: 2026-07-23
- Constraint: no private proxy/futures loading, no real-data execution or P&L, no optimization, no active DTR changes, no shared execution extraction, no Pine implementation
- Input boundary: frozen synthetic integration from merge `d055b9f4f53510300e9be3375501c7143899c325`
- Source policy: `SYNTHETIC_DUKASCOPY_INDEX_CFD_PROXY_FIXTURE`; Decimal directional-pessimistic normalization; exact timestamp/activity preservation; no gap repair
- Status: normalization policy preregistered; implementation and adversarial synthetic review in progress
