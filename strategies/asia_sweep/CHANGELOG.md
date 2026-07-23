# Asia Sweep Changelog

## v0.1.0 — 2026-07-23

### Added

- Created a standalone Asia Sweep strategy namespace, branch and file structure.
- Added a hard separation contract preventing use of the active DTR signal engine and evidence folders.
- Added NQ and ES development manifests with explicit qualification states.
- Added deterministic event-ledger models for aggressive reclaim, wick-qualified reclaim, displacement and failed-retest variants.
- Added causal entry timestamps, raw stop/target construction and rejection-reason logging.
- Added a prefix-replay causality validator.
- Added a separate eight-test synthetic suite outside the default DTR test path.
- Added roadmap, preregistration, strategy specification, work package, claim, handover and reviewer report.

### Reason

The Asia high/low sweep hypothesis is a distinct strategy, not a DTR filter or entry module. It therefore requires independent data, signals, tests, evidence and promotion decisions.

### Validation

- Python syntax compilation passed.
- Separate synthetic suite: 8 passed.
- Existing DTR files and active signal logic were not edited.

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
- Connect an isolated execution adapter only after event audit and causality review.
- Run WP-AS-07 development research after preregistration is frozen.
