# Asian Sweep Early-Entry Research Roadmap

Date: 2026-07-26  
Status: `INFORMATION_FRONTIER_CLOSED_NEGATIVE`

## Completed

### Phase 1 — causal landmark information frontier

- T0, T1, T2 and T3 landmark semantics frozen;
- exact validated `LEGACY_T5` benchmark retained;
- next-active BID/ASK execution geometry reconstructed;
- separate elastic-net and nonlinear models fitted at each landmark;
- 2015–2019 leave-one-year-out evaluation completed;
- pair, year, side, weekday, calibration, quintile and Hit@1 evidence retained;
- independent source, timing, geometry and metric audit completed.

Decision:

`FAIL_EARLY_ENTRY_INFORMATION_FRONTIER_STOP_BEFORE_POLICY_PNL`

## Closed path

The following one-shot formulation is closed:

> Select a single fixed entry landmark from T0–T3 with a landmark-specific midpoint-reversal probability, then optimize position management.

No pre-T5 landmark had both enough predictive separation and enough remaining midpoint reward/risk.

## Reserved position structures

The following structures remain valid research concepts but were not opened in this programme:

- `TP1_50_RUNNER_50`;
- `TP1_25_RUNNER_75`;
- `NO_TP1_FULL_RUNNER`.

They may only be tested inside a new programme whose predictive objective and entry architecture pass their own gate. They may not be applied retrospectively to this failed landmark family.

## Next research priorities

### Priority 1 — continuation/fake-rejection triage

Build a direct three-state model:

1. successful reversal;
2. same-direction continuation after failed rejection;
3. unresolved or abstain.

The target must be defined from executable post-landmark first passage rather than by inverting the reversal probability.

Required work:

- freeze continuation barrier and horizon;
- classify false reversal separately from immediate continuation;
- build causal T0–T3 and `LEGACY_T5` populations;
- grouped development and external validation;
- probability conflict/abstention policy;
- no P&L until the triage model validates.

### Priority 2 — true staged information entry

Test an architecture that does not choose one fixed landmark:

- small provisional risk at T0 or T1;
- retain/add only when later causal evidence improves;
- reduce/cancel immediately when continuation evidence develops;
- total day risk capped at 1R;
- no T5 feature available early;
- sizing ladder and cancellation rules frozen before P&L.

This programme must use its own target and must not import a failed runner policy.

### Priority 3 — target-specific extended-reversal model

A no-TP1/full-runner structure should be paired with a model trained for the extended target it is intended to capture.

Candidate research question:

> Conditional on an Asian sweep and causal reversal evidence, what identifies moves that continue to 2R–4R or a structural opposing-liquidity target later in the day?

This is distinct from predicting the Asian midpoint. It must freeze:

- target family;
- horizon;
- unresolved/ambiguous handling;
- feature snapshot;
- grouped selection;
- the 50%, 25% and 0% midpoint structures.

### Priority 4 — external transfer

Because 2015–2019 has now been used for early-entry development, genuinely independent evidence must come from:

- protected 2020–2021 only after a new contract passes development;
- 2022–2025 only through the original sequential gates;
- or additional FX pairs under a preregistered transfer design.

## Prohibited rescues

- no T2/T3 threshold tuning on the current evidence;
- no EURUSD-only promotion;
- no weekday, side or range-width filtering;
- no partial fraction search on the failed landmark population;
- no alternative stop or target grid inside this branch;
- no Pine, alerts, paper trading or deployment.

## Current programme status

- reversal fingerprint: validated;
- post-T5 midpoint execution: rejected;
- fixed 50/50 staged exit: rejected;
- long-runner grid: rejected;
- one-shot T0–T3 entry frontier: rejected;
- continuation triage: planned, not yet executed;
- true staged information entry: planned, not yet executed;
- target-specific full-runner model: planned, not yet executed.
