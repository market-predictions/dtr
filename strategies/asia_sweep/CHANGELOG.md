# Asia Sweep Changelog

## v0.4.0 — 2026-07-23

### Added

- Added timezone-aware UTC-to-`America/New_York` proxy loading with DST-safe wall-calendar session construction.
- Added separate source-activity auditing alongside exact one-minute grid integrity.
- Added the frozen activity gate: at least one active minute and no inactive run longer than 10 minutes.
- Added causal pre-signal activity metadata and distinct integrity failure scope/reasons.
- Added a private real-data event-audit workflow for both registered proxies.
- Added deterministic 50-event samples, clean-room event reconstruction and private five-minute OHLC evidence.

### Changed

- Enabled the registered proxy manifests for event-ledger-only research while keeping execution and P&L blocked.
- Made observed signal eligibility depend only on source data available through the determining bar.
- Preserved descriptive full-window activity without allowing future inactivity to erase an earlier decision.
- Required `entry_timestamp < execution_window_end` for all variants.

### Corrected during review

- Corrected a London boundary defect that could emit a 05:55 bar as a 06:00 entry.
- Replaced elapsed-time date arithmetic with explicit local wall-calendar construction across DST weekends.
- Separated stale carry-forward quotes from missing timestamp-grid records.
- Corrected cross-run artifact download and canonical `prepared/` staging paths.
- Added retained private OHLC paths after review found event rows alone insufficient for manual audit evidence.
- Applied Ruff's exact formatting correction for one over-length test line.

### Reason

Event semantics must be reproducible before any execution or performance research. Timestamp identity, source activity and half-open entry boundaries are part of the strategy definition, not data-cleaning details, and future source conditions may not change an already observable event.

### Validation

- Development event ledgers: 3,120 records per proxy across four preregistered variants.
- Deterministic audit samples: 50 NQ-proxy and 50 ES-proxy records.
- Independent clean-room reconstruction: 100/100 exact, zero mismatches.
- NQ private OHLC evidence: 6,900 five-minute rows.
- ES private OHLC evidence: 6,888 five-minute rows.
- Repository Ruff and tests passed on Python 3.11 and 3.12.
- Isolated Asia Sweep tests passed on Python 3.11 and 3.12.
- Both private event-audit jobs passed source verification, reconstruction and no-P&L enforcement.
- No execution simulation, P&L, optimization or variant selection was performed.

### Known limits

- No neutral post-entry execution adapter exists.
- Same-minute collisions, gaps and time exits are not implemented.
- CME futures timestamp, continuous-contract, roll, volume, cost and fill validation remain unresolved.
- Provider authorization for future automated proxy acquisition remains unresolved.
- The independent review is a same-session clean-room pass, not an external human audit.

### Next

- Freeze a neutral execution contract in a separate work package.
- Add synthetic same-minute stop/target, entry-stop, gap and time-exit tests.
- Reproduce the locked DTR benchmark before extracting shared execution utilities.
- Keep all real-data P&L disabled until the execution package is independently reviewed and merged.

## v0.3.0 — 2026-07-23

### Added

- Added controlled static-BI5 acquisition tooling for Dukascopy USATECH and USA500 index-CFD proxies.
- Added deterministic full-grid ZIP and GZIP archives with SHA-256 inventory records.
- Added dedicated NQ-proxy and ES-proxy manifests with hard event-runner blocks.
- Added offset-aware New York timestamps while retaining UTC as the authoritative clock.
- Added `is_active_quote` metadata and a frozen source-activity/staleness contract.
- Added a manifest guard that prevents unresolved proxy adapters from entering event generation.
- Added qualification, clean-room review and handover records for the private proxy registration.

### Changed

- Replaced the rate-limited package API with the previously qualified static daily BI5 transport.
- Replaced positive-volume-only normalization with complete quote-grid retention.
- Restored the ordinary isolated Asia Sweep CI after all eight yearly acquisition jobs completed.
- Classified provider authorization as unresolved and prohibited publication or redistribution of market data.

### Corrected during review

- Corrected BI5 field interpretation to seconds, open, close, low, high and volume.
- Replaced `datetime.timezone.utc` with `datetime.UTC` for repository Ruff compliance.
- Prevented DST ambiguity by serializing New York timestamps with explicit UTC offsets.
- Disclosed a one-row USATECH source revision and a five-row USA500 active-count drift.
- Corrected the final canonical USA500 count to 1,348,073 positive-volume rows.

### Reason

Proxy data can support market-structure research only when quote continuity, source activity, timezone semantics and proxy-versus-futures limitations remain explicit. Zero-volume carry-forward rows are neither missing bars nor proof of tradability, so they must be retained and audited separately.

### Validation

- Eight yearly acquisition jobs passed for 2022–2025.
- Each proxy retains exactly 2,103,840 unique, on-grid UTC minutes.
- Zero duplicate timestamps, off-grid rows, non-one-minute adjacency gaps and OHLC violations.
- Canonical normalized artifact digest: `sha256:1ebbac7dd92bd61c21988102b227d7e706ba51e3669e4f3c4aa647fa48d1276e`.
- Original repository CI passed on the acquisition head.
- Isolated Asia Sweep CI passed on Python 3.11 and 3.12.
- No P&L, optimization or combined DTR/Asia result was generated.

### Known limits

- The proxy timezone/activity adapter is not implemented.
- The event ledger can still emit an entry at execution-window end.
- Official no-P&L proxy event ledgers and 50-event audits are not complete.
- Provider authorization for future automated acquisition remains unresolved.
- CFD proxy data cannot validate CME futures roll, volume, costs or fills.

### Next

- Implement UTC-to-New-York proxy loading and the frozen activity gate.
- Correct the end-of-window entry boundary with adversarial tests.
- Generate official no-P&L event ledgers for both proxies.
- Audit at least 50 events per proxy.
- Keep execution simulation and P&L blocked until event semantics are frozen.

## v0.2.0 — 2026-07-23

### Added

- Added exact half-open one-minute interval auditing.
- Added Asia-range, full-window and pre-signal completeness metadata to every event.
- Added a strict Asia Sweep ZIP/CSV adapter that does not silently drop duplicates or the final date.
- Added explicit source-schema fields to the NQ manifest; ES remains blocked until registered.
- Expanded the isolated suite from 9 to 25 tests.
- Added full pytest-report artifacts before the isolated CI gate is enforced.

### Changed

- A partial Asia range is now `INELIGIBLE`.
- Missing data before the determining signal bar now blocks the setup.
- A future gap after a valid signal is recorded but cannot retrospectively remove that signal.
- `NO_SWEEP` is emitted only after a complete execution window.
- AS-C now requires a complete causal 20-bar body reference.
- Duplicate timestamps now fail loudly instead of being silently deduplicated.

### Corrected during review

- Replaced the inherited source loader because it silently deduplicated timestamps and removed the final date.
- Renamed the Asia interval-integrity test module to avoid a pytest import collision with DTR's existing `test_integrity.py`.
- Applied Ruff's exact import-format correction.

### Reason

The strategy cannot be evaluated honestly unless the range, signal path and source records are complete at the time each decision becomes observable. Future data-quality events must not alter prior signal decisions.

### Validation

- Python syntax compilation passed locally.
- Isolated Asia Sweep suite: 25 passed locally.
- Dedicated Asia Sweep CI passed on Python 3.11 and 3.12.
- Original repository CI passed, including Ruff and existing DTR tests.
- Independent published-diff review verdict: `APPROVE_DATA_INTEGRITY_FOR_MERGE_BLOCK_EVENT_RESULTS_AND_PNL`.
- No P&L or historical strategy result was generated.

### Known limits

- Qualified raw NQ and ES files are not available in the active workspace for event generation.
- NQ timestamp labeling and continuous-contract construction remain unresolved.
- ES data and schema remain unregistered.
- Manual 50 NQ + 50 ES event audit remains blocked.
- Post-entry execution and causal gap liquidation are not connected.

### Next

- Acquire and register qualified ES data.
- Resolve or preregister NQ timestamp-interpretation sensitivity.
- Generate event ledgers without P&L.
- Complete the manual event audit.
- Freeze event semantics before adding execution.

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

The Asia high/low sweep hypothesis is a distinct strategy, not a DTR filter or entry module. It therefore requires independent data, signals, tests, manifests, reports, validation and promotion decisions.

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
