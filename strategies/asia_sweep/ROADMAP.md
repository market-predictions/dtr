# Asia Sweep Standalone Strategy — Research Roadmap

**Strategy ID:** `ASIA_SWEEP_STANDALONE_V0`  
**Repository:** DTR Optimization Lab  
**Isolation:** `SEPARATE_STRATEGY_SEPARATE_EVIDENCE`  
**Instruments:** NQ and ES  
**Signal bars:** five-minute  
**Execution source:** one-minute  
**Deployment:** prohibited

This roadmap implements the accepted Asia-range sweep research plan as a strategy distinct from Daytrading Rauf. It may borrow audited DTR infrastructure and registered data, but it has independent signal logic, tests, manifests, reports, validation and promotion decisions. The detailed user-approved source roadmap is the basis for this canonical repository version. fileciteturn32file0

## Research question

Does a sweep beyond the completed Asia-session high or low, followed by failure to accept outside the range, produce a stable and executable reversal edge in NQ and ES after realistic costs?

The strategy family tests four interpretations:

- AS-A: aggressive same-bar reclaim;
- AS-B: wick-qualified reclaim;
- AS-C: opposing displacement confirmation;
- AS-D: causal failed-retest confirmation.

The simple reclaim is the control. The research question is whether wick, displacement or failed-retest confirmation adds incremental value.

## Hard separation rules

- Development branch: `agent/asia-sweep-standalone-foundation`.
- Governance, manifests, reports and tests: `strategies/asia_sweep/`.
- Code: `src/dtr_lab/strategies/asia_sweep/`.
- Runner: `scripts/run_asia_sweep_manifest.py`.
- Never call `dtr_lab.research.engine.generate_signals()`.
- Never alter the active DTR candidate or locked evidence for Asia Sweep needs.
- Never write Asia Sweep outputs into DTR result directories.
- Never combine Asia Sweep with DTR before standalone validation.
- Never use a rejected variant or DTR module to rescue another strategy.

## Phase 0 — Protect DTR and establish isolation

**Status:** foundation implemented; canonical DTR rerun pending CI/full checkout.

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

Use half-open windows. Include Monday through Friday initially and report weekdays separately. Maximum one trade per instrument per execution window; first valid signal wins; no same-window re-entry in the primary specification.

## Phase 2 — Qualify NQ and ES data

**Status:** NQ development reference registered with unresolved timestamp/roll status; ES blocked.

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

Headline NQ/ES comparisons use only the intersection of qualified dates. A source with unresolved timestamp or roll construction may support ingestion and descriptive development, but not decisive validation.

## Phase 3 — Shared infrastructure boundary

**Status:** signal boundary complete; neutral execution adapter pending.

Permitted reuse:

- registered market data;
- checksum verification;
- generic one-minute loading;
- generic five-minute resampling;
- causal generic features;
- later, neutral conservative execution and reporting utilities.

Prohibited reuse:

- DTR signal generation;
- DTR selected configuration;
- DTR result and promotion logic.

## Phase 4 — Event ledger and manual audit

**Status:** initial deterministic event ledger implemented; completeness and gap metadata pending.

Store one record per instrument/date/window, including no-sweep and rejected events. Minimum content includes Asia range, swept side, sweep timestamp and depth, candle morphology, reclaim, displacement, failed retest, entry, stop, target, status and rejection reason.

Before P&L:

- inspect at least 50 NQ events;
- inspect at least 50 ES events;
- cover both directions and windows;
- include DST, roll-adjacent, missing-data and same-bar edge cases;
- retain deterministic OHLC/chart evidence.

## Phase 5 — Preregistered variants

### AS-A aggressive reclaim

A five-minute bar penetrates the Asia level by at least two ticks and closes back inside. Entry occurs only after that candle closes.

### AS-B wick-qualified reclaim

AS-A plus rejection-wick ratio at least 0.50 and direction-adjusted close-location value at least 0.60.

### AS-C displacement

AS-A plus an opposing candle within three bars. Its body is at least 1.25 times the causal trailing median body, the close passes the sweep-candle midpoint, and price remains back inside the Asia range.

### AS-D failed retest

AS-A plus a right-side-confirmed reaction swing, a later retest that stays inside the original sweep extreme, and a later close through the confirmed reaction swing.

### Primary risk model

- stop: two ticks beyond original sweep extreme;
- target: 2.0R;
- full-position exit;
- no partial, runner or breakeven move;
- time exit at execution-window end.

## Phase 6 — Causality and adversarial tests

**Status:** initial eight-test suite passed locally; full twenty-case suite pending.

Required coverage includes threshold edges, no reclaim, double sweep, wick boundary, displacement timing, causal pivot confirmation, same-minute stop/target collision, entry-stop collision, missing gaps before and during trades, DST, roll boundaries, simultaneous NQ/ES signals and deterministic repeated output.

For every emitted signal, truncate data at the entry timestamp and reproduce the same decision. Any change under prefix replay is a lookahead failure.

## Phase 7 — Controlled development research

**Blocked until Phases 2, 4 and 6 pass.**

Partitions:

- development: 2023-01-01 through 2024-06-30;
- historical validation: 2024-07-01 through 2025-03-31;
- later historical research: 2025-04-01 through 2025-12-11.

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

`APPROVE_FOUNDATION_WITH_BLOCKERS_BEFORE_PNL`

Proceed next with data qualification, session/gap completeness and manual event audit. Do not calculate or inspect strategy P&L until those contracts are frozen.
