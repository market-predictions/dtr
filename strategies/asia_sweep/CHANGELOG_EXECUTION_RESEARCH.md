# Asian Sweep Execution Research Changelog

## v2.0.4 — 2026-07-26

- **Changed:** Closed the 2015–2019 executable-strategy discovery with `FAIL_DISCOVERY_STOP_BEFORE_EXECUTION_VALIDATION`.
- **Reason:** All three preregistered entry variants produced negative expectancy, poor annual/pair breadth, excessive drawdown, weak bootstrap evidence and negative cost-stressed expectancy.
- **Known limits:** The result applies to the T5 entry family with Asian-midpoint target and the original `0.20 × range` adverse barrier. It does not test earlier staged execution or direct continuation trading.
- **Next:** Preserve later execution partitions unopened; route new hypotheses to separate preregistered branches.

## v2.0.3 — 2026-07-26

- **Changed:** Added independent raw BID/ASK reconstruction of every filled trade and order state.
- **Reason:** Distinguish economic failure from simulator, quote-side, expiry, ordering or arithmetic defects.
- **Known limits:** M1 data cannot identify the true intrabar sequence when both stop and target trade in one bar; the contract intentionally assumes stop first.
- **Next:** Retain the conservative fill policy in any future execution programme.

## v2.0.2 — 2026-07-26

- **Changed:** Added dedicated Actions workflow, pair artifacts, pooled decision artifact, calendar-week bootstrap, cost stress and attribution tables.
- **Reason:** Make the execution decision reproducible and auditable from immutable source/model artifacts.
- **Known limits:** Workflow is computationally heavier because it restores full BID/ASK M1 source partitions.
- **Next:** Convert to manual-only reproduction after scientific closure.

## v2.0.1 — 2026-07-26

- **Changed:** Froze pending-limit cancellation and replacement by a later eligible same-pair event.
- **Reason:** Prevent simultaneous pending orders and hindsight selection when multiple signals occur before 10:00.
- **Known limits:** The rule is conservative and may cancel an earlier order that would subsequently have filled.
- **Next:** Preserve unchanged for all comparisons in the closed execution family.

## v2.0.0 — 2026-07-26

- **Changed:** Created the executable reversal research contract and BID/ASK simulator.
- **Reason:** Test whether the validated T5 midpoint-prediction mechanism leaves positive tradable expectancy after legal entry, spread, stop distance and time constraints.
- **Known limits:** Only three fixed entry variants; no partial exits, trailing stops, pair filters, threshold tuning or portfolio sizing.
- **Next:** Run frozen 2015–2019 discovery and stop before later partitions when no variant passes.
