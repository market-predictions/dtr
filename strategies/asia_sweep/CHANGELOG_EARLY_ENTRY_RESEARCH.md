# Asian Sweep Early-Entry Research — Full Changelog

## v5.4.0 — 2026-07-26

### Changed

- completed the source-backed T0–T3 information-payoff frontier;
- evaluated elastic-net and HGB candidates in five leave-one-year-out folds;
- added the exact frozen `LEGACY_T5` benchmark;
- retained all predictions, breadth tables, weekly rankings and executable geometry;
- recorded decision `FAIL_EARLY_ENTRY_INFORMATION_FRONTIER_STOP_BEFORE_POLICY_PNL`;
- added independent source/quote/geometry/metric audit;
- closed the work package before position-policy P&L;
- made the expensive workflow manual-reproduction-only.

### Reason

No one-shot early landmark combined sufficient reversal discrimination with sufficient remaining reward/risk to the Asian midpoint.

### Known limits

- the predictive target remains midpoint-first reversal, not extended intraday reversal;
- phase-2 50%, 25% and 0% midpoint structures were not opened;
- 2020–2025 remains protected and unopened;
- 2015–2019 is development evidence, not untouched validation.

### Next

- direct reversal/continuation/abstention triage;
- true staged provisional-entry and cancellation architecture;
- target-specific extended-reversal model before full-runner testing.

## v5.3.0 — 2026-07-26

### Changed

- froze three grouped inner folds by Amsterdam ISO week;
- froze elastic-net and HGB hyperparameter grids;
- froze fold-local preprocessing and Platt calibration;
- froze year-block probability quintiles;
- bound `LEGACY_T5` to development model run `30177831134`.

### Reason

Ensure the authoritative source-backed frontier could not alter its optimizer, calibration or ranking rules after outcome inspection.

### Known limits

- calibration is evaluated on pooled outer predictions but is not used to retune thresholds;
- models are intentionally compact rather than exhaustive.

### Next

- run source-backed frontier once under the frozen operations.

## v5.2.0 — 2026-07-26

### Changed

- clarified T0–T3 semantics;
- renamed the old validation snapshot `LEGACY_T5`;
- specified exact next-active-minute entry timing;
- froze resolved-event exclusion and active-minute delays.

### Reason

The historical `T5` implementation uses a five-bar inclusive window ending normally at sweep minute `m+4`, not five complete post-sweep bars.

### Known limits

- inactive quote gaps can make the elapsed entry delay exceed one minute;
- the benchmark name is retained for historical traceability.

### Next

- implement causal landmark ledger with explicit timestamps.

## v5.1.0 — 2026-07-26

### Changed

- added mandatory conditional position structures:
  - 50% TP1 / 50% runner;
  - 25% TP1 / 75% runner;
  - no TP1 / full runner;
- separated landmark discovery from position-policy selection;
- froze attribution and complexity tie-break rules.

### Reason

The user required smaller partial profit-taking and a full-position runner to be considered without allowing those variants to contaminate entry selection.

### Known limits

- structures remain conditional on a passing early landmark;
- final target, horizon and stop families require a separate amendment.

### Next

- complete phase-1 landmark gate before opening policy P&L.

## v5.0.0 — 2026-07-26

### Changed

- opened clean early-entry branch from the pre-runner execution codebase;
- preregistered T0, T1, T2, T3 and T5 information-versus-payoff analysis;
- blocked P&L until an early landmark passed;
- protected 2020–2025;
- created work package and claim.

### Reason

Validated T5 prediction did not convert into stable P&L because too much favorable movement occurred before entry.

### Known limits

- no execution policy defined;
- no continuation model included;
- no deployment work authorized.

### Next

- build causal landmark snapshots and grouped out-of-fold models.
