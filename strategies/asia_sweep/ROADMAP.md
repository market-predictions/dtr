# Asia Sweep Standalone Strategy — Research Roadmap

**Strategy ID:** `ASIA_SWEEP_STANDALONE_V0`  
**Repository:** DTR Optimization Lab  
**Isolation:** `SEPARATE_STRATEGY_SEPARATE_EVIDENCE`  
**Instruments:** NQ and ES  
**Signal bars:** five-minute  
**Execution source:** one-minute  
**Deployment:** prohibited

This roadmap implements the accepted Asia-range sweep research plan as a strategy distinct from Daytrading Rauf. It may borrow audited DTR infrastructure and registered data, but it has independent signal logic, tests, manifests, reports, validation and promotion decisions. The detailed user-approved source roadmap is the basis for this canonical repository version.

## Research question

Does a sweep beyond the completed Asia-session high or low, followed by failure to accept outside the range, produce a stable and executable reversal edge in NQ and ES after realistic costs?

The strategy family tests four interpretations:

- AS-A: aggressive same-bar reclaim;
- AS-B: wick-qualified reclaim;
- AS-C: opposing displacement confirmation;
- AS-D: causal failed-retest confirmation.

The simple reclaim is the control. The research question is whether wick, displacement or failed-retest confirmation adds incremental value.

## Hard separation rules

- Development branches are phase-specific; current normalization work uses `agent/asia-sweep-proxy-normalization-contract`.
- Governance, manifests, reports and tests: `strategies/asia_sweep/`.
- Code: `src/dtr_lab/strategies/asia_sweep/`.
- Runner: `scripts/run_asia_sweep_manifest.py`.
- Never call `dtr_lab.research.engine.generate_signals()`.
- Never alter the active DTR candidate or locked evidence for Asia Sweep needs.
- Never write Asia Sweep outputs into DTR result directories.
- Never combine Asia Sweep with DTR before standalone validation.
- Never use a rejected variant or DTR module to rescue another strategy.

## Phase 0 — Protect DTR and establish isolation

**Status:** foundation and both CI tracks complete; direct canonical DTR data replay remains pending before shared execution extraction.

- Create separate branch and namespace.
- Record separation contract.
- Preserve active DTR files unchanged.
- Before extracting shared execution infrastructure, reproduce the locked DTR benchmark exactly: 495 trades, 86.00476134576057R net and 14.10785751380752R maximum drawdown.
- Any unexplained DTR regression blocks shared-infrastructure work.

## Phase 1 — Freeze strategy specification

**Status:** foundation specification and preregistration committed.

Primary sessions in `America/New_York`:

- Asia range: 18:00 previous day to 02:00 trade date;
- London: 02:00–06:00;
- New York: 08:30–11:30.

Use half-open windows. Include Monday through Friday initially and report weekdays separately. The first qualifying sweep in each execution window owns the event. If it fails reclaim or confirmation, a later sweep may not replace it. Maximum one trade per instrument per execution window; no same-window re-entry in the primary specification.

## Phase 2 — Qualify NQ and ES data

**Status:** private Dukascopy NQ and ES proxy snapshots are structurally qualified, checksummed and enabled for event-only research through the frozen timezone/activity adapter. CME futures timestamp, continuous-contract, roll, volume, cost and fill validation remain unresolved.

Each instrument needs:

- source and licence;
- checksum;
- timezone and bar-label semantics;
- first/last timestamp;
- missing and duplicate bar audit;
- incomplete-session audit;
- individual-contract metadata or documented continuous-contract method;
- roll dates and adjustment method;
- tick size, point value and commissions.

The Asia-specific source adapter rejects duplicate and off-grid timestamps and does not silently remove the final date. The canonical proxy archives retain the complete one-minute quote grid, keep UTC authoritative, convert causally to offset-aware New York timestamps and separate quote continuity from source activity. The frozen activity gate requires a complete one-minute interval, at least one positive-volume minute and no zero-volume run longer than 10 minutes.

The proxy snapshots may support descriptive market-structure and event-semantic research. They do not establish CME futures roll, volume, cost, fill or deployment validity. Headline NQ/ES comparisons use only the intersection of qualified dates.

## Phase 3 — Shared infrastructure boundary

**Status:** signal boundary, strict source adapter, manifest execution guard, proxy event adapter, synthetic neutral execution, event-to-execution integration and synthetic proxy normalization are complete. Private normalization audit and real proxy/futures execution remain blocked.

Permitted reuse:

- registered market data;
- checksum verification;
- generic five-minute resampling;
- causal generic features;
- the standalone synthetic neutral-execution contract through the frozen integration adapter;
- the reviewed `DIRECTIONAL_PESSIMISTIC_V1` synthetic proxy normalization contract;
- later, neutral reporting utilities.

Prohibited reuse:

- DTR signal generation;
- DTR source-loader repairs that conceal duplicates or incomplete dates;
- DTR selected configuration;
- DTR result and promotion logic;
- shared DTR execution extraction before exact locked-benchmark replay;
- direct real-data calls into the synthetic execution simulator;
- mixed-instrument execution under one economics configuration;
- private normalization or execution before a protected no-P&L audit package passes.

## Phase 4 — Event ledger and manual audit

**Status:** official no-P&L proxy ledgers, deterministic 50-event samples per proxy, independent clean-room reconstruction and private five-minute OHLC evidence are complete. Proxy event semantics are frozen; real-data execution and P&L remain blocked.

Store one record per instrument/date/window, including no-sweep and rejected events. Minimum content includes Asia range, interval-integrity status, swept side, sweep timestamp and depth, candle morphology, reclaim, displacement, failed retest, entry, stop, target, status and rejection reason.

Causal integrity rules:

- an incomplete Asia range is ineligible;
- missing or stale source data before the determining signal bar blocks the event;
- a future data-quality event cannot retroactively erase an observable signal;
- `NO_SWEEP` requires a complete and active execution window;
- an entry timestamp must be strictly earlier than execution-window end.

Completed before P&L:

- 50 NQ-proxy records independently reconstructed;
- 50 ES-proxy records independently reconstructed;
- all four variants, both directions and both windows represented;
- DST, stale-data, no-activity, ambiguous-sweep and boundary cases retained;
- complete private five-minute OHLC paths retained for every sampled Asia range and execution window;
- 100/100 sampled events reproduced exactly without calling the production signal builder.

## Phase 5 — Preregistered variants

### AS-A aggressive reclaim

A five-minute bar penetrates the Asia level by at least two ticks and closes back inside. Entry occurs only after that candle closes.

### AS-B wick-qualified reclaim

AS-A plus rejection-wick ratio at least 0.50 and direction-adjusted close-location value at least 0.60.

### AS-C displacement

AS-A plus an opposing candle within three bars. Its body is at least 1.25 times the causal trailing median body, the close passes the sweep-candle midpoint, and price remains back inside the Asia range. The median is computed from a complete 20-bar causal history and does not reset at the London or New York window boundary.

### AS-D failed retest

AS-A plus a right-side-confirmed reaction swing, a later retest that stays inside the original sweep extreme, and a later close through the confirmed reaction swing.

### Primary risk model

- stop: two ticks beyond original sweep extreme;
- target: 2.0R;
- full-position exit;
- no partial, runner or breakeven move;
- time exit at execution-window end.

## Phase 6 — Causality and adversarial tests

**Status:** signal, data, manifest, proxy event, synthetic execution, event-to-execution integration and synthetic proxy normalization coverage pass in dedicated Python 3.11/3.12 CI; original repository Ruff/tests pass independently. Private normalization evidence, real execution and portfolio-level cases remain pending.

Completed signal/event coverage includes threshold edges, no reclaim, double sweep, wick boundaries, displacement timing and pre-window warmup, causal pivot confirmation, first-sweep ownership, incomplete ranges, missing pre-signal data, future gaps, duplicate timestamps, deterministic output, instrument-neutral signal semantics, blocked-manifest handling, activity-staleness boundaries, DST-aware proxy conversion and entry exactly at window end.

Completed synthetic execution coverage includes exact-minute entry, missing/inactive entry, gap-through-stop, one-tick risk, entry/later stop-target collisions, long/short stop and target gaps, missing-minute liquidation, first-active-quote handling, 10/11-minute inactivity boundaries, first-unsafe-condition precedence, unresolved paths, time exits, slippage, commission, target-RR lock, input immutability and prefix replay.

Completed integration coverage includes all four variants, long/short mapping, UTC/New York and DST wall-calendar conversion, local-date and half-open-window membership, strict tick grids, one-instrument economics, stable identity keys, event-contract digests, event-bound minute fixtures, duplicate/missing/orphan/malformed frame-map rejection, batch/row equality, order invariance, immutability and integrated prefix replay.

Completed normalization coverage includes exact provider-symbol and BID-side binding, locked policy identity, Decimal source-grid operations, directionally pessimistic long/short normalization, derived-target noise canonicalization, risk-collapse rejection, raw OHLC validation, timestamp/gap/activity preservation, source/event/frame digests, wrong-source and stale-payload rejection, source-row order invariance and compatibility with the frozen WP5 binding. The complete isolated suite contains 223 passing tests.

Future coverage must include protected private normalization evidence, futures-valid basis and instrument economics, roll boundaries, MFE/MAE reporting and simultaneous NQ/ES portfolio constraints.

For every emitted signal or completed synthetic exit, truncate data at the determining timestamp and reproduce the same decision. Any change under prefix replay is a lookahead failure.

## Phase 7 — Controlled development research

**Blocked until a protected private normalization-only audit passes and a later real-execution package is separately preregistered and reviewed. Real-data execution and P&L remain prohibited.**

Partitions:

- development: 2023-01-01 through 2024-06-30;
- historical validation: 2024-07-01 through 2025-03-31;
- later historical research: 2025-04-01 through 2025-12-31.

The latter partitions are historical lockboxes, not pristine OOS.

Report NQ, ES and matched-date pooled results; London/New York; long/short; year; weekday; range-width, sweep-depth and entry-hour buckets; one-, two- and four-tick stress; MFE, MAE, holding time and time-exit rate.

Do not tune NQ and ES separately. Only contract economics and provenance may differ.

## Phase 8 — Ablations and null models

Compare:

- Asia-level touch without reclaim;
- AS-A reclaim;
- AS-B wick filter;
- AS-C displacement;
- AS-D failed retest;
- direction-matched random entries in the same windows;
- time-matched non-sweep entries;
- shuffled sweep-date assignments preserving weekday/window frequency.

Use session-date and month-block bootstrap, paired differences versus AS-A and familywise-aware interpretation across the four declared variants.

## Phase 9 — Locked historical validation

After selecting at most one primary variant, freeze code, manifest and dataset checksums. Run locked periods once and report every result.

Continuation requires all of the following:

1. positive expectancy in NQ;
2. positive expectancy in ES;
3. pooled expectancy at least 0.08R;
4. positive pooled expectancy after two-tick stress;
5. profit factor at least 1.15;
6. at least 80 locked-evaluation trades per instrument;
7. no instrument contributes more than 70% of pooled net R;
8. no year contributes more than 50% of pooled net R;
9. no window-by-weekday cell contributes more than 50% of net R;
10. no unresolved data/roll cluster explains more than 20% of net R;
11. results are directionally stable under plausible timestamp interpretations;
12. the finalist beats AS-A where additional confirmation is claimed;
13. the result survives familywise-aware interpretation.

Passing authorizes fresh-OOS research only.

## Phase 10 — DTR redundancy and diversification study

Only after standalone validation, compare identical-date Asia Sweep and DTR ledgers for signal overlap, direction agreement, return and drawdown correlation, unique trades, marginal return/drawdown contribution and equal-risk combined equity.

Reject as redundant when overlap and correlation are high and the combination adds no stability. Retain separately only when Asia Sweep is independently positive and contributes distinct returns or drawdown diversification.

## Phase 11 — Fresh OOS

Freeze one candidate before inspecting fresh NQ/ES data. Do not use fresh OOS to choose among AS-A through AS-D. A pass permits paper research, not deployment.

## Phase 12 — TradingView parity

After Python validation, build Pine Script v6 with the same sessions, state machine, costs, stop/target and timestamps. Require trade-for-trade parity on signal, direction, entry, stop, target, exit, reason and R result.

## Current decision

`SYNTHETIC_PROXY_NORMALIZATION_FROZEN_PRIVATE_EXECUTION_AND_PNL_BLOCKED`

The synthetic proxy normalization contract may merge after final exact-head repository CI, isolated Asian Sweep CI and unchanged private no-P&L event-audit stability gates pass. Proceed next only with a protected private normalization-only audit package. That package may inspect raw-versus-normalized evidence but must not call execution or calculate P&L. Real proxy/futures execution remains blocked until normalization evidence, source limitations and instrument economics are independently reviewed.
