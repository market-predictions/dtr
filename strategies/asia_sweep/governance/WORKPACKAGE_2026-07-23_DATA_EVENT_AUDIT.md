# Work Package AS-WP-20260723-01 — Data Integrity and Event Audit

## Objective

Make Asia Sweep event eligibility causal and data-quality aware before any historical P&L is calculated.

## Scope

- exact one-minute coverage auditing for half-open intervals;
- complete Asia-range requirement;
- complete data path from execution-window start through the determining signal bar;
- causal handling of gaps after a valid signal;
- complete-window requirement before classifying a window as `NO_SWEEP`;
- duplicate and off-grid timestamp detection;
- event-ledger integrity metadata;
- complete causal 20-bar displacement reference;
- remaining signal-level adversarial tests;
- independent review of the published diff.

## Explicit causality rules

1. A missing minute in the completed Asia range makes the date/window ineligible.
2. A missing minute before or within the determining signal bar makes the setup ineligible.
3. A data gap after a valid signal may be recorded but may not retrospectively remove the signal.
4. `NO_SWEEP` may be assigned only after a complete execution window is observed.
5. Post-entry missing data will later be handled by causal execution liquidation, not retrospective trade deletion.

## Out of scope

- historical P&L;
- trade execution simulation;
- ES source registration;
- manual 50 NQ + 50 ES chart audit without the raw datasets;
- parameter tuning;
- DTR/Asia portfolio comparison.

## Acceptance criteria

1. Integrity metadata are present on every event record.
2. Partial Asia ranges cannot produce signals or `NO_SWEEP` classifications.
3. Missing pre-signal data block signals.
4. Future gaps do not alter already observable signal decisions.
5. Duplicate timestamps fail loudly rather than being silently deduplicated.
6. AS-C requires a complete causal 20-bar reference.
7. At least 20 isolated tests pass on Python 3.11 and 3.12.
8. Original DTR CI remains green.
9. No P&L is emitted.

## Current status

Implementation and synthetic validation are complete locally. Historical event generation and the manual audit remain blocked because qualified NQ/ES raw data are not available in the active workspace.
