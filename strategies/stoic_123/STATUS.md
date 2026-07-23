# Status — Stoic Edge 1-2-3

Date: 2026-07-23
Version: `v0.3.0-research-preregistered`
Active work package: `STOIC123-WP-20260723-02`
Decision state: `NQ_LONG_ONLY_MECHANISM_VALIDATION_PREREGISTERED`

## Completed evidence

- Separate causal Stoic namespace, governance tree, runner, and frozen six-arm phase-one family.
- Qualified NQ futures, `NQ_PROXY`, `ES_PROXY`, and GBPUSD source contracts.
- GBPUSD phase one rejected: all six arms negative.
- NQ and ES proxy phase one completed separately with independent ledger reconstruction.
- Five of six arms were positive on each index proxy, but every date-block interval crossed zero.
- Strict close remains the strongest cross-proxy robustness candidate; no strategy is promoted.
- Repository Ruff and full tests passed on Python 3.11 and Python 3.12 for v0.2.0.

## Direction-counterfactual correction

The informal long-only counterfactual disabled short entries and unintentionally disabled opposite short management signals as well. That altered both entry direction and the exit system.

`STOIC123-WP-20260723-02` supersedes that interpretation:

- long-only means long entries only;
- the management detector remains two-directional;
- an opposite short 1-2-3 may still exit a long;
- all 18 corrected ledgers passed independent arithmetic, chronology, risk, overlap, and direction review;
- only the no-map controls changed; the NQ EMA-map and strict-close candidates were unchanged;
- no earlier counterfactual artifact may be promoted.

## Active frozen validation

Candidates:

1. no-map full-sequence benchmark;
2. EMA-map primary candidate;
3. strict-close secondary candidate;
4. EMA-plus-breakout diagnostic candidate.

The study compares both-direction, long-only, short-only, EMA-break-only, EMA-break-plus-retest, and matched-time controls on the checksum-qualified NQ futures archive. It also runs cost, entry-delay, chronological, session, concentration, and exposure tests.

## Execution state

- Design and promotion gates frozen before NQ futures performance inspection.
- Dedicated runner and 26 focused regression tests implemented locally.
- Source bounds, source/config checksums, event geometry, management direction, matched-control coverage, and independent reconstruction are hard gates.
- Registered public source reacquisition workflow prepared.
- Historical execution pending exact archive checksum confirmation.

## Scientific restrictions

- No DTR baseline or DTR result is changed.
- No Stoic threshold, timeframe, session, stop, target, or exit optimization.
- No pooled instrument result.
- No CFD proxy relabelling as CME futures.
- No Pine, sizing, deployment, alert, or profitability authorization.
