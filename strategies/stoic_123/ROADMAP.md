# Stoic Edge 1-2-3 Roadmap

## Phase 0 — Isolation and preregistration

Status: **complete**

- [x] Create a separate branch, namespace, runner, governance tree, and result contract.
- [x] Preserve all DTR baselines and signal code unchanged.
- [x] Freeze the six-arm phase-one family before performance inspection.
- [x] Label USA500 as `ES_PROXY`, not CME ES futures.

## Phase 1 — Mechanical baseline engine

Status: **complete; data execution pending**

- [x] Implement close-based Step 1 beyond EMA 10/20.
- [x] Implement retest logic and a causal post-retest base.
- [x] Lock the Step-2 boundary before any Step-3 bar.
- [x] Implement close-confirmed Step 3 and next-open execution.
- [x] Implement protective stop, gap liquidation, single-position sequencing, and costs.
- [x] Implement opposite complete 1-2-3 management exit.
- [x] Add synthetic tests and independent trade-ledger reconstruction.
- [ ] Execute the frozen family on the qualified NQ and `ES_PROXY` files.

## Phase 2 — Integrity and descriptive evidence

Status: **blocked on phase-one data run**

- [ ] Audit event counts through the full funnel.
- [ ] Inspect examples without changing definitions.
- [ ] Report session, direction, weekday, year, hold-time, exit-reason, and cost attribution.
- [ ] Confirm no positions bridge unsafe data gaps.
- [ ] Confirm no overlapping positions within each instrument stream.

## Phase 3 — Robustness, not optimization

Status: **not started**

- [ ] Run nearby predeclared timing sensitivity: 3/5/10-minute execution and 15/30/60-minute management.
- [ ] Stress one, two, and four ticks per side.
- [ ] Run chronological folds and date-block bootstrap.
- [ ] Test boundary definition sensitivity: wick boundary versus close boundary.
- [ ] Test maximum base age and base compression without searching unrestricted grids.

## Phase 4 — Mechanism review

Status: **not started**

- [ ] Determine whether any edge comes from the map, Step 1 impulse, base compression, or generic breakout exposure.
- [ ] Compare against matched random-time and simple EMA-break controls.
- [ ] Quantify redundancy versus existing DTR opportunities and trade timing.
- [ ] Reject the strategy if the map adds no material information or the sequence reduces to an ordinary breakout with worse execution.

## Phase 5 — Cross-market evidence

Status: **not started**

- [ ] Compare NQ and `ES_PROXY` without pooling returns or tuning by instrument.
- [ ] Acquire actual contract-audited ES futures data when available.
- [ ] Repeat the frozen finalist on actual ES before any ES claim.
- [ ] Extend NQ with qualified fresh and longer-history data.

## Phase 6 — Selection gate

Status: **not started**

A candidate may advance only if it is causal, cost-resilient, chronologically stable, not driven by one session/year, and materially useful relative to simpler controls. Otherwise record `STOP_RESEARCH` or retain only as a descriptive chart-study tool.

## Phase 7 — TradingView parity

Status: **blocked**

- [ ] Port only a data-supported finalist to Pine Script v6.
- [ ] Reconcile Python and Pine events one-for-one.
- [ ] Make repainting, higher-timeframe completion, and delayed confirmation explicit.
- [ ] Add alerts only after parity passes.

## Phase 8 — Paper-forward observation

Status: **blocked**

- [ ] Freeze the finalist.
- [ ] Observe forward without retuning.
- [ ] Compare actual slippage and missed fills with the research assumptions.
- [ ] Require a new decision gate before any production use.
