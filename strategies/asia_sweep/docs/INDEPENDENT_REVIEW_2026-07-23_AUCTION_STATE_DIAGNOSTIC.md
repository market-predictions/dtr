# Independent Review — Auction-State Diagnostic

Date: 2026-07-23  
Work package: `AS-WP-20260723-08`

## Scope

Review the session-specific auction-state engine, corrected private diagnostic artifact and promotion decision without reopening the protected validation period or adding post-hoc filters.

## Findings

### Causal review

Two defects were identified before acceptance:

1. The opposite-side sweep check originally ended at the frozen three-bar decision window instead of the actual rejection-confirmation bar. A second-side breach occurring during confirmation could therefore be missed.
2. Fixed one-minute horizons originally included the bar beginning exactly at the horizon endpoint, adding one unintended minute.

Both defects were corrected, regression-tested and re-run on both private proxies. The earlier artifact was superseded.

### Exact-head gates

On head `ab785b8a1eb44ae9c0e21ced31bedfb57e3a3b29`:

- repository CI passed;
- isolated Asia Sweep Python 3.11 and 3.12 tests passed;
- the unchanged proxy event audit passed;
- NQ and ES private diagnostic jobs passed;
- raw private sources were removed before artifact upload;
- aggregate boundary and no-P&L guards passed.

### Independent result reconstruction

The corrected combined ledger contained 1,436 unique event identities with no observation on or after 2024-07-01. Independent grouping reproduced:

- London external-liquidity rejection: 32 NQ and 23 ES observations;
- positive 30-minute and 60-minute means in both proxies, but insufficient sample and intervals spanning zero;
- negative New York external rejection;
- failure of London compressed acceptance on cross-instrument 60-minute consistency;
- material 2024-H1 decay in New York compressed acceptance;
- no passing mechanism/session cell.

### Promotion review

The aggregate decision `NO_MECHANISM_PASSES_DEVELOPMENT_PROMOTION_STANDARD` follows directly from the preregistered criteria. No validation access, challenger construction, weekday/direction selection or threshold optimization is justified from this package.

## Verdict

`APPROVE_CORRECTED_DIAGNOSTIC_CLOSE_BROAD_AUCTION_STATE_LINE`

A narrowly separate PDH/PDL–Asian-boundary cluster study may proceed only under a new work package with its distance and Asian-range regime frozen before executable outcomes are inspected.
