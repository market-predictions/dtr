# Changelog — DTR-CROSSMARKET-WP-20260722-18

## v0.4.0-research.18 — 2026-07-22

### Added

- Provider-neutral NQ and Dukascopy USA500 one-minute source adapters.
- Canonical bar-open Eastern Time normalization with daylight-saving conversion.
- Frozen NQ-versus-USA500 comparison period and session contract.
- Parallel original-E6 and E6-no-FOMC arms using one shared signal and execution engine.
- Instrument-specific tick value, commission, coverage and gap-handling contracts.
- Comparable opportunity, funnel, trade, year, session, direction, cost and uncertainty outputs.
- Exact NQ regression gates preventing hidden engine drift.
- Independent reconstruction and deterministic repeat evidence.
- Automated tests for proxy gap handling, E6 threshold semantics, cost geometry and replication classification.

### Research result

- NQ E6 reproduced exactly: 304 trades, 48.937550R and 0.160979R expectancy.
- NQ E6 no-FOMC reproduced exactly: 291 trades, 53.483342R and 0.183792R expectancy.
- USA500 E6: 281 trades, 13.330895R and 0.047441R expectancy.
- USA500 E6 no-FOMC: 268 trades, 12.981512R and 0.048438R expectancy.
- USA500 E6 expectancy fell to -0.011853R at two ticks per side.
- Proxy performance was concentrated in London: +31.13R; Asia and New York were negative.
- The no-FOMC overlay added 4.55R on NQ but reduced proxy total return by 0.35R after exact resequencing.

### Decision

- Record `PARTIAL_COST_FRAGILE_REPLICATION`.
- Retain original E6 and E6 no-FOMC unchanged.
- Do not create a proxy-specific London rule or modify the FOMC policy from this study.
- Do not pool NQ and proxy returns or describe the proxy as CME ES futures.

### Known limitations

- USA500 is a bid-CFD proxy without historical ask prices or observed spread.
- Dukascopy volume is not CME centralized volume.
- Proxy data contains no ES contract rollover behavior.
- The proxy date-block expectancy interval crosses zero broadly.
- NQ timestamp and continuous-contract methodology remain unresolved.

### Next

- Extend the unchanged framework to materially longer USA500 history.
- Acquire actual contract-audited ES futures one-minute data when feasible.
- Run qualified fresh or longer-history NQ evidence without retuning.
