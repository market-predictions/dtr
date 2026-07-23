# Asia Sweep Changelog

## v0.1.0 — 2026-07-23

### Added

- Created a standalone Asia Sweep strategy namespace, branch and file structure.
- Added a hard separation contract preventing use of the active DTR signal engine and evidence folders.
- Added NQ and ES development manifests with explicit qualification states.
- Added deterministic event-ledger models for aggressive reclaim, wick-qualified reclaim, displacement and failed-retest variants.
- Added causal entry timestamps, raw stop/target construction and rejection-reason logging.
- Added a prefix-replay causality validator.
- Added a separate nine-test synthetic suite outside the default DTR test path.
- Added a dedicated Asia Sweep CI workflow for Python 3.11 and 3.12.
- Added roadmap, preregistration, strategy specification, work package, claim, handover and reviewer report.

### Corrected during review

- Changed AS-C displacement-body normalization from an execution-window-local median to a causal trailing median computed from all available preceding five-minute bars.
- Added an early-London regression proving that pre-window bars seed the displacement reference without future data.
- Reformatted new Python files to comply with the repository's 100-character Ruff limit.

### Reason

The Asia high/low sweep hypothesis is a distinct strategy, not a DTR filter or entry module. It therefore requires independent data, signals, tests, evidence and promotion decisions.

### Validation

- Python syntax compilation passed locally.
- Separate synthetic suite: 9 passed locally.
- Dedicated Asia Sweep CI passed on Python 3.11 and 3.12.
- Original repository CI passed, including the Ruff gate and existing DTR tests.
- Branch comparison remains additive: no existing DTR file is modified or deleted.

### Known limits

- No P&L execution adapter is connected.
- NQ timestamp semantics and continuous-contract construction remain unresolved.
- ES data are not registered in the repository.
- Manual chart audit of 50 NQ and 50 ES events is not complete.
- No historical or fresh OOS result exists.

### Next

- Register qualified ES data.
- Add DTR baseline golden-regression execution to the branch gate.
- Add gap/session completeness checks to the event ledger.
- Complete the remaining adversarial tests.
- Connect an isolated execution adapter only after event audit and causality review.
- Run WP-AS-07 development research after preregistration is frozen.
