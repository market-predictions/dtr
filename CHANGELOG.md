# Changelog

## Unreleased — 2026-07-21

### Added

- Dukascopy data-source viability review with technical, legal, provenance, and promotion gates.
- Phase 0B provider-neutral market-data acquisition roadmap.
- A staged pilot basket for FX, metals, and U.S. index-CFD structural proxies.
- Cross-market sequencing that tests the frozen DTR candidate before allowing asset-specific retuning.

### Decision

- Keep the existing NQ futures dataset as the frozen primary baseline for the current reversal candidate.
- Do not adopt the legacy `giuse88/duka` package as a production dependency.
- Prefer a native Python adapter over approved official Dukascopy API access.
- Use a pinned `dukascopy-node` result as an independent comparison oracle during the pilot.
- Treat Dukascopy index CFDs as structural proxies rather than CME futures substitutes.

### Why

Dukascopy can provide broader history and cross-asset coverage, but provider, timestamp, bid/ask, spread, session, volume, and instrument semantics must remain explicit. Integrating the source through a provider-neutral contract adds cross-market research capacity without contaminating the frozen NQ baseline or implying that broker-CFD results validate futures execution.

### Known limitations

- Approved Dukascopy API access and automation/data-use rights have not yet been documented for this project.
- No live acquisition pilot or canonical Dukascopy dataset has yet passed the DTR integrity gate.
- Dukascopy index-CFD prices, activity volume, spreads, sessions, and contract semantics are not equivalent to CME futures.
- Energy commodities and equities are deferred until the first pilot basket establishes reliable normalization.

### Next

- Confirm approved API access and applicable data-use terms.
- Implement the provider interface, canonical schema, fixtures, caching, checksums, and provider-specific audits.
- Run the controlled pilot after the current NQ data-integrity gate without interrupting the NQ reversal and continuation workstreams.

## v0.2.1 — 2026-07-21

### Added

- Strict Pydantic research-manifest schema.
- Dataset SHA-256 verification before a research run.
- Frozen candidate manifest for `DTR_PY_NQ_CANDIDATE_0_1`.
- Deterministic manifest runner.
- Generated CSV, Parquet, JSON, funnel, half-year, session, weekday, and direction artifacts.
- Code, manifest, and dataset provenance in each run summary.
- Frozen-baseline regression checks for trade count, net R, and maximum drawdown.
- Manifest and checksum integrity tests.

### Changed

- TradingView is formally parked as the primary research environment.
- The roadmap now prioritizes Python reproducibility, data integrity, continuation research, context ablation, adaptive routing, and later Pine implementation.
- Repository documentation now describes manifest-driven research runs.

### Why

The first optimized reversal result must be reproducible from one versioned command before additional modules or parameter searches are trusted. This release turns the candidate from a documented result into a machine-checkable research specification.

### Known limitations

- The full candidate rerun still requires the local Kaggle dataset because raw market data is excluded from Git.
- Continuous-contract rollover and back-adjustment semantics remain unresolved.
- Timestamp semantics remain provisional.
- Continuation, IFVG/CISD, H1Vol, Weekly VWAP, higher-timeframe scoring, and footprint are not yet included.

### Next

- Execute and lock the manifest-driven candidate rerun.
- Classify data gaps and probable rollover discontinuities.
- Add safeguards around unexplained gaps.
- Begin the independent continuation engine after the reproducibility gate passes.

## v0.2.0 — 2026-07-21

### Added

- Python reversal research and execution engine.
- Session ranges, sweeps, reclaims, protected pivots, BOS/MSS, acceptance, and entries.
- Regime, session, weekday, risk, stop, target, and time-close variants.
- Staged optimization packs for BOS, sweep, regime, timing, risk, and exits.
- First 904-configuration NQ research run.
- Half-year, session, weekday, direction, cost-stress, walk-forward, and Monte Carlo results.
- Initial research candidate `DTR_PY_NQ_CANDIDATE_0_1`.

### Why

The known DTR concept can be tested more thoroughly in Python than through repeated manual TradingView configuration changes.

### Known limitations

- The engine is a research interpretation rather than an exact Pine clone.
- No pristine post-research holdout or paper-forward data is available yet.

### Next

- Make the research result reproducible through a strict manifest and regression gate.

## v0.1.0 — 2026-07-21

### Added

- Initial DTR Optimization Lab repository structure.
- Python packaging and dependency configuration.
- Data-safe `.gitignore` that excludes raw market data and generated artifacts.
- NQ one-minute dataset catalog with checksum, schema, date range, and audit findings.
- CSV/ZIP loader with strict schema validation.
- OHLCV resampling utility for one-minute to five-minute research bars.
- Deterministic dataset audit model and command-line interface.
- Unit tests for audit and resampling semantics.
- GitHub Actions CI for Python 3.11 and 3.12.

### Why

The DTR strategy requires systematic funnel diagnostics and controlled optimization outside TradingView. The first release established reproducible data handling before strategy research.

### Known limitations

- Contract rollover and back-adjustment semantics were unresolved.
- Source timestamps were timezone-naive pending bar-open/bar-close verification.
- The uploaded dataset appeared capped at the Excel worksheet row limit and ended mid-session.
- No DTR strategy logic had been ported yet.

### Next

- Complete the NQ dataset integrity and contract-continuity audit.
- Implement session-range and sweep primitives.
- Build the baseline setup funnel before testing parameter alternatives.
