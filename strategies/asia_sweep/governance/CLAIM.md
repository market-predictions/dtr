# Active Claim

- Work package: `AS-WP-20260723-05`
- Branch: `agent/asia-sweep-event-execution-integration`
- Claimed scope: synthetic event-to-execution mapping, strict price-grid policy and deterministic replay gate
- Started: 2026-07-23
- Constraint: no private proxy/futures execution, no real-data P&L, no optimization, no active DTR changes, no shared execution extraction, no Pine implementation
- Input boundary: frozen event semantics from merge `cf9a09db7a80a53c24b92164e1474b01553781f2` and frozen synthetic execution from merge `9a1ba6628589084f90ff19b1dcdb7db080601c5b`
- Source policy: `SYNTHETIC_EVENT_PACKET` plus `SYNTHETIC_TEST_FIXTURE`; strict tick-grid inputs; no rounding or source conversion
- Status: integration contract preregistered; adapter and deterministic replay tests in progress
