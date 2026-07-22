# Handover — DTR-CROSSMARKET-WP-20260722-18

## Status

Parallel framework, first execution, independent review and deterministic repeat complete.

## Decision

`PARTIAL_COST_FRAGILE_REPLICATION`

## Reusable framework

- Provider-neutral instrument specifications and adapters: `src/dtr_lab/research/cross_market.py`.
- Executable parallel runner: `scripts/run_nq_usa500_parallel.py`.
- Frozen preregistration: `results/2026-07-22/nq_usa500_parallel_preregistration.json`.
- NQ E6 and E6 no-FOMC remain mandatory regression gates.
- Instrument performance is never pooled.

## Main results

### NQ

- E6: 304 trades, 48.937550R, 0.160979R expectancy, 8.632571R maximum drawdown.
- E6 no-FOMC: 291 trades, 53.483342R, 0.183792R expectancy, 9.151061R maximum drawdown.

### USA500 proxy

- E6: 281 trades, 13.330895R, 0.047441R expectancy, 17.377216R maximum drawdown.
- E6 no-FOMC: 268 trades, 12.981512R, 0.048438R expectancy, 16.304286R maximum drawdown.
- E6 two-tick expectancy: -0.011853R.
- Date-block E6 95% interval: approximately -0.097R to +0.197R.

## Attribution

- Proxy London: +31.13R.
- Proxy Asia: -7.23R.
- Proxy New York: -10.57R.
- No-FOMC policy delta: +4.55R on NQ, -0.35R on proxy after resequencing.

## Restrictions

Do not:

- tune proxy thresholds, sessions, weekdays or event definitions;
- create a London-only proxy strategy from this sample;
- pool NQ and proxy returns;
- describe USA500 as CME ES futures;
- infer live sizing, Pine or deployment authorization.

## Next valid work

1. Extend the same USA500 framework to materially longer history without parameter changes.
2. Acquire actual contract-audited ES futures one-minute data and run the same arms.
3. Acquire qualified fresh NQ or longer contract-audited NQ history.

Delete temporary raw USA500 data after the authorized proxy research sequence is complete.
