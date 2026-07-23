# Asia Sweep Separation Contract

## Decision

`SEPARATE_STRATEGY_SEPARATE_EVIDENCE`

Asia Sweep is not a DTR module, DTR filter, DTR entry route or DTR candidate revision. It is a separate strategy stored in the same repository for operational convenience.

## Permitted reuse

The strategy may reuse stable infrastructure when the dependency is explicit and does not embed DTR alpha logic:

- registered raw market data;
- checksum verification;
- generic one-minute ingestion;
- generic five-minute resampling;
- generic feature calculations when their lookback is causal;
- generic cost and conservative intrabar execution primitives after extraction behind a neutral interface;
- generic reporting and bootstrap utilities.

## Prohibited coupling

- importing or calling `dtr_lab.research.engine.generate_signals`;
- changing `StrategyConfig`, `CandidateSignal` or active DTR manifests for Asia Sweep needs;
- writing Asia Sweep artifacts into DTR result directories;
- using DTR-selected weekdays, sessions or thresholds as Asia Sweep defaults without independent preregistration;
- mixing Asia Sweep and DTR returns before standalone validation;
- describing Asia Sweep results as improvements to the DTR baseline;
- allowing an Asia Sweep failure to alter the frozen DTR decision.

## File boundaries

- governance, manifests, roadmap, changelog, reports and tests: `strategies/asia_sweep/`;
- implementation: `src/dtr_lab/strategies/asia_sweep/`;
- runner: `scripts/run_asia_sweep_manifest.py`;
- generated artifacts: `strategies/asia_sweep/reports/<run_id>/`.

## Test boundaries

DTR tests remain under the repository's default `tests/` path. Asia Sweep tests live under `strategies/asia_sweep/tests/` and run with their own `pytest.ini`.

A future neutral infrastructure extraction must first reproduce the locked DTR benchmark exactly. Any unexplained DTR trade or metric change blocks the extraction.
