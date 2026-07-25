# Stacey Burke FX Research Roadmap

## Programme decision

Status: **complete — rejected at Gate B**

Decision: `FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME`

The frozen previous-day sweep-and-reclaim event was common, but its 60-minute reversal outcome did not outperform matched controls. This roadmap is closed without strategy construction or holdout inspection.

## Phase 0 — Source universe and governance

Status: **complete**

- [x] Freeze a factor-diverse ten-pair FX universe.
- [x] Separate the Stacey Burke namespace from DTR, Asian Sweep and Stoic.
- [x] Define annual/YTD BID/ASK source and integrity contracts.
- [x] Acquire and qualify 2015–2025 plus 2026 YTD.
- [x] Freeze annual/YTD BID/ASK hashes before event-return inspection.
- [x] Preserve source and compact qualification evidence independently.

## Phase 1 — Conditional event census

Status: **complete — passed**

- [x] Freeze a causal previous-day high/low sweep-and-reclaim definition.
- [x] Use DST-safe New York FX days and London event windows.
- [x] Require a normalized 5% ATR20 excursion and reclaim within 15 minutes.
- [x] Report event frequency before any trading-rule construction.
- [x] Pool the ten-pair universe with pair/factor attribution.
- [x] Enforce sample-size, breadth and concentration gates.

Result:

- 2,423 retained 2015–2021 events;
- all ten pairs and four factor blocks represented;
- census authorized the controlled event study.

## Phase 2 — Controlled discovery event study

Status: **complete — failed Gate B**

- [x] Freeze one primary 60-minute reversal-signed endpoint.
- [x] Match five distinct-date controls per event.
- [x] Match within pair/year/weekday/15-minute London bucket.
- [x] Match on pre-event 15-minute return and 60-minute realized volatility.
- [x] Use calendar-date block bootstrap inference.
- [x] Use date-clustered matched-set permutation inference.
- [x] Retain pair and factor-block attribution.
- [x] Independently reconstruct the final evidence.

Result:

- 2,393 matched events and 11,965 controls;
- pooled mean effect `-0.001709 ATR20`;
- 95% date-block interval `[-0.010309, +0.006900]`;
- clustered permutation p-value `0.670733`;
- four positive pairs and one positive factor block;
- one of six scientific gates passed.

Decision: reject the tested reversal mechanism.

## Phase 3 — 2022–2023 event-study validation

Status: **cancelled by Gate B failure**

- [ ] Validation not executed.
- [x] 2022–2023 outcomes remain uninspected.

The frozen contract prohibited validation after a discovery failure.

## Phase 4 — SB-1 executable candidate

Status: **not authorized**

No entry, stop, expiry, target, management, executable BID/ASK simulation or strategy P&L may be designed for this failed family.

## Phase 5 — Holdout and prospective monitoring

Status: **not authorized for this family**

- 2024–2025 remains untouched.
- 2026 YTD remains monitoring-only.
- No Pine, alerts, paper trading or deployment is authorized.

## Phase 6 — Additional Burke families

Status: **not authorized as rescue variants**

SB-2 or SB-3 may not be introduced as retrospective replacements for SB-1. Any future Burke-related programme requires:

- a genuinely different mechanism;
- independent theoretical motivation;
- a new preregistration;
- a new trial budget;
- evidence not selected to rescue the failed sweep-and-reclaim hypothesis.

See `FINAL_DECISION.md` for the complete result and audit record.