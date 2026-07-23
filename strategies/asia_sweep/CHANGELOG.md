# Asia Sweep Changelog

## v0.6.0 — 2026-07-23

### Added

- Added a strict standalone event-to-execution integration adapter.
- Added deterministic SHA-256 stable event identities.
- Added separate SHA-256 digests for all execution-relevant event facts.
- Added one-instrument-per-configuration economics binding.
- Added event-bound synthetic minute-frame sealing by identity and payload digest.
- Added deterministic packet replay sorted by stable event key.
- Added explicit output columns for configured tick size, point value, commission and slippage.
- Added integrated prefix replay for every packet row.
- Expanded the isolated Asia Sweep suite to 185 tests.

### Changed

- Required every packet event to match the instrument bound to its execution economics.
- Required event timestamps to be timezone-aware, one-minute aligned, on the declared trade date and inside the declared half-open execution window.
- Required event entry, stop, target and every one-minute OHLC value to lie on the configured tick grid.
- Required minute-frame dictionaries to contain exactly the expected lowercase SHA-256 keys.
- Kept stable identity separate from execution-payload revisions so row identity can remain fixed while contract drift remains visible.
- Kept the integration package synthetic-only and disconnected from manifests, private data and real-data execution.

### Corrected during review

- Prevented mixed NQ-like and ES-like events from silently sharing one point value, commission and slippage schedule.
- Prevented a generic synthetic minute fixture from being swapped between events without detection.
- Added payload-digest rejection for changed stop, target, direction or timestamp under an unchanged identity key.
- Added strict local-date and execution-window membership checks.
- Rejected fractional, boolean and non-finite directions.
- Rejected missing or non-string identity values and malformed frame-map keys.
- Applied the pinned Ruff model-import order exactly and removed the temporary diagnostic workflow.

### Reason

A frozen signal and a frozen execution simulator are not sufficient unless the bridge between them is deterministic, instrument-specific and auditable. Event identity, event payload, minute-frame ownership and execution economics must remain distinct so a replay cannot silently use the wrong data path, wrong point value or revised event geometry.

### Validation

- Isolated Asia Sweep suite: 185 passed on Python 3.11.
- Isolated Asia Sweep suite: 185 passed on Python 3.12.
- Repository Ruff passed on the reviewed implementation head.
- Full repository tests passed on Python 3.11 and 3.12 on the reviewed implementation head.
- All four preregistered variants map without selection.
- Long and short mapping, UTC/New York conversion and DST wall-calendar mapping passed.
- One-instrument economics separation passed.
- Swapped-frame, same-identity payload-drift and malformed-key rejection passed.
- Batch replay equaled independent row replay and remained invariant to input order.
- Target and data-gap integrated prefix replay passed.
- Branch changes remain confined to standalone Asia Sweep code, tests and governance.
- No private proxy/futures execution, real-data P&L, optimization or variant ranking was performed.
- Final exact-head repository CI, isolated CI and unchanged no-P&L event-audit stability remain required before merge.

### Known limits

- The integration path remains synthetic-only.
- No proxy-to-futures price normalization or tick translation exists.
- No private proxy or CME futures source is connected to execution.
- Real-data MFE, MAE, holding-time, P&L and portfolio reporting remain blocked.
- CME timestamp, continuous-contract, roll, volume, spread, commission and fill validity remain unresolved.
- Provider authorization for future automated proxy acquisition remains unresolved.
- Repository-wide NumPy/pandas timedelta deprecation warnings remain warning debt.
- The independent review is a same-session clean-room pass, not an external human audit.

### Next

- Design a separate proxy execution-source adapter under a new work package.
- Freeze source identity, price normalization, instrument economics and unresolved-exit behavior before connecting private data.
- Add synthetic adversarial tests for proxy tick translation and source-bound replay.
- Reproduce the locked DTR benchmark before extracting any shared execution utility.
- Keep all real-data P&L disabled until the proxy adapter is independently reviewed and merged.

## v0.5.0 — 2026-07-23

### Added

- Added an isolated one-minute execution simulator under the standalone Asia Sweep namespace.
- Added immutable execution signal, configuration and outcome models.
- Added explicit blocked, exited and unresolved execution states with deterministic reasons.
- Added adverse entry, stop and market-exit slippage and separate round-trip commission accounting.
- Added stop-first entry-minute and later-minute collision handling.
- Added stop-gap, target-gap, missing-minute, stale-activity and exact time-exit logic.
- Added a hard synthetic-fixture workflow guard and prefix-replay validation.
- Added 37 direct execution/precedence tests within an isolated suite of 146 tests.

### Changed

- Locked execution target construction to the preregistered 2.0R.
- Made the one-minute open at the exact signal timestamp the only eligible entry bar.
- Kept the signal-layer stop fixed and recalculated target distance from actual slipped entry risk.
- Required missing-data liquidation to wait for the first subsequent active quote.
- Preserved the first unsafe source condition when stale activity precedes later missing data.
- Kept blocked and unresolved paths free of manufactured return values.

### Corrected during review

- Rewrote two adversarial fixtures that did not isolate their claimed one-tick-risk and 11-minute-stale boundaries.
- Applied pinned Ruff import ordering exactly and removed the temporary diagnostic workflow.
- Added finite-value, OHLC-invariant, timestamp-grid and timezone-awareness validation.
- Prevented inactive carry-forward quotes from being used as missing-data liquidation fills.
- Prevented later missing timestamps from overwriting an already-unsafe stale-path reason.
- Removed arbitrary target-RR variation from the synthetic execution input.

### Reason

Execution semantics must be frozen independently of strategy outcomes. Exact entry timing, conservative intrabar ordering, unsafe-data liquidation, time exits and explicit costs determine whether a signal can be evaluated without lookahead or hidden optimism. Keeping the simulator synthetic-only prevents performance feedback from influencing this contract.

### Validation

- Isolated Asia Sweep suite: 146 passed on Python 3.11.
- Isolated Asia Sweep suite: 146 passed on Python 3.12.
- Repository Ruff passed.
- Full repository tests passed on Python 3.11 and 3.12.
- Prefix replay passed for target, stop, data-gap, stale-activity and time exits.
- Long/short stop-gap and target-gap symmetry passed.
- Unmarked frames, duplicate timestamps, off-grid timestamps, non-finite prices and invalid OHLC fail loudly.
- Branch comparison changes only standalone Asia Sweep execution, tests and governance.
- No real proxy/futures execution, P&L, optimization or variant selection was performed.

### Known limits

- No event-ledger-to-execution adapter exists.
- The synthetic marker is an accidental-use guard, not a security boundary.
- Proxy/futures price-grid normalization is not implemented.
- Real-data MFE, MAE, portfolio constraints and reporting are not implemented.
- CME futures timestamp, continuous-contract, roll, volume, cost and fill validation remain unresolved.
- Existing NumPy/pandas timedelta deprecation warnings remain repository-wide warning debt.
- The independent review is a same-session clean-room pass, not an external human audit.

### Next

- Add a separate event-to-execution integration and deterministic replay gate.
- Freeze price-grid and source-kind mapping before any real-data execution.
- Prove event ledgers remain unchanged when mapped into execution inputs.
- Reproduce the locked DTR benchmark before extracting any shared execution utility.
- Keep all real-data P&L disabled until the integration package is independently reviewed and merged.

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
