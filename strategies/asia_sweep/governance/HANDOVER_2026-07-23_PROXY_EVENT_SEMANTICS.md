# Handover — AS-WP-20260723-03

## Delivered

- timezone-aware UTC-to-`America/New_York` proxy loading;
- DST-safe local wall-calendar session construction;
- separate one-minute grid and source-activity integrity audits;
- frozen one-positive-minute and 10-minute maximum stale-run gate;
- causal pre-signal activity decisions;
- non-retroactive treatment of future source inactivity;
- strict half-open entry boundary;
- distinct integrity failure scope and reasons;
- event-only NQ-proxy and ES-proxy manifests;
- four official no-P&L development ledgers per proxy;
- deterministic 50-event sample per proxy;
- independent clean-room reconstruction of all 100 sampled records;
- private five-minute OHLC evidence for every sampled Asia range and execution window;
- dedicated private workflow with source removal before artifact upload;
- repository and isolated CI validation on Python 3.11 and 3.12;
- no P&L, optimization, DTR combination or market-data commit.

## Event inventory

### NQ proxy

- AS-A: 212 signals, 509 rejected, 45 no-sweep, 14 ineligible;
- AS-B: 59 signals, 662 rejected, 45 no-sweep, 14 ineligible;
- AS-C: 108 signals, 613 rejected, 45 no-sweep, 14 ineligible;
- AS-D: 11 signals, 710 rejected, 45 no-sweep, 14 ineligible.

### ES proxy

- AS-A: 151 signals, 555 rejected, 60 no-sweep, 14 ineligible;
- AS-B: 48 signals, 658 rejected, 60 no-sweep, 14 ineligible;
- AS-C: 83 signals, 623 rejected, 60 no-sweep, 14 ineligible;
- AS-D: 18 signals, 688 rejected, 60 no-sweep, 14 ineligible.

These are variant event counts, not executed trades or returns.

## Validation

- independent NQ reconstruction: 50/50 exact;
- independent ES reconstruction: 50/50 exact;
- late NQ AS-C confirmation at 06:00 rejected correctly;
- future ES stale-run cases preserve earlier causal signals;
- no duplicate event keys or cross-variant drift in shared event fields;
- no execution/P&L fields;
- exact-head normal and isolated CI green;
- private audit workflow run: `30003836567`;
- NQ artifact digest: `sha256:54d3bbe10b256a3d41f5afb173c5540b1b389c0c01d9eb9e557e436c85bfe883`;
- ES artifact digest: `sha256:7e091227df36879fd9eed5c5ad4cb11653db59eb6b8fe4379c91ba1af4d197d5`.

## Not delivered

- post-entry execution simulation;
- same-minute collision policy implementation;
- gap liquidation or time exits;
- P&L, optimization or variant selection;
- historical validation or fresh OOS;
- DTR diversification analysis;
- CME futures confirmation;
- provider-authorization resolution;
- TradingView/Pine implementation.

## Decision

`PROXY_EVENT_SEMANTICS_FROZEN_EXECUTION_AND_PNL_BLOCKED`

The event-semantic package is mergeable. It authorizes a separate neutral-execution design work package only. It does not authorize strategy performance research.

## Next work package

`AS-WP-20260723-04 — Neutral Execution Contract and Adversarial Simulator Tests`

Required order:

1. freeze entry-price, stop, target, time-exit and cost semantics;
2. implement one-minute post-entry execution without DTR signal coupling;
3. enforce conservative same-minute stop/target and entry-stop handling;
4. implement unsafe-gap liquidation and explicit reason logging;
5. add time-exit behavior at each execution-window end;
6. add synthetic adversarial and prefix-causality tests;
7. reproduce the locked DTR benchmark before extracting shared execution utilities;
8. keep all real-data P&L disabled until the execution review merges.
