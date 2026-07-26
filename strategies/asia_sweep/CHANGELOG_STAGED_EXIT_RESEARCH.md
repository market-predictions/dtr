# Asian Sweep Staged-Exit Research Changelog

## v3.0.3 — 2026-07-26

- Changed: retired the source-backed staged-exit workflow to manual reproduction only.
- Reason: discovery reached a terminal negative decision; automatic reruns would add cost and could obscure the frozen first result.
- Known limits: the workflow intentionally enforces a passing decision and therefore ends red when reproducing the negative result.
- Next: preserve evidence; do not open later staged-exit partitions.

## v3.0.2 — 2026-07-26

- Changed: recorded `FAIL_STAGED_EXIT_DISCOVERY_STOP_BEFORE_VALIDATION` and complete leg, pair, year and exit-state attribution.
- Reason: neither original-stop nor break-even runner management passed discovery gates.
- Known limits: only a 50/50 split, opposite-boundary TP2 and 11:00 runner time exit were tested.
- Next: treat any alternative split, target or horizon as a new hypothesis.

## v3.0.1 — 2026-07-26

- Changed: fixed a synthetic selection fixture and removed one unused import.
- Reason: the fixture produced zero drawdown and Ruff detected a non-functional import; neither affected market logic.
- Known limits: synthetic tests validate mechanics, not market profitability.
- Next: execute frozen source-backed discovery.

## v3.0.0 — 2026-07-26

- Changed: added a spread-aware staged-exit simulator with TP1 and runner leg accounting.
- Reason: the Asian midpoint should be evaluated as a first target rather than assumed to be the only target.
- Known limits: entry remains the first active market minute after complete T5 confirmation.
- Next: compare original runner stop versus next-bar break-even.

## v2.0.0 — 2026-07-26

- Changed: completed the predecessor 100%-at-midpoint execution study.
- Reason: determine whether the validated T5 fingerprint was directly executable.
- Known limits: full liquidation at the midpoint did not test continuation beyond TP1.
- Next: staged-exit research authorized as a separate hypothesis.
