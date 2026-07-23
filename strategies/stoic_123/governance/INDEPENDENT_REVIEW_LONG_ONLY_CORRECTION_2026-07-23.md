# Independent Review — Corrected Long-Only Counterfactual

Date: 2026-07-23
Scope: corrected NQ-proxy, ES-proxy, and GBPUSD long-only executions
Verdict: `APPROVE_CORRECTION_SUPERSEDE_ORIGINAL_COUNTERFACTUAL`

## Review method

A separate review pass checked all 18 corrected instrument-arm ledgers for:

- published trade count versus ledger count;
- net-R and expectancy reconstruction from trade rows;
- positive initial risk;
- signal, entry, and exit chronology;
- base-lock time strictly before signal time;
- absence of overlapping positions;
- entry-direction restriction;
- retention of both-direction management-event generation.

## Result

All 18 corrected ledgers passed. The mapped arms were byte-equivalent at the trade level to their earlier exploratory long-only runs. Only the no-map controls changed:

- NQ proxy: +1.614024R versus the flawed run;
- ES proxy: +7.864794R versus the flawed run;
- GBPUSD: +17.284629R and three additional later long trades after earlier exits freed the single-position sequence.

The changes are consistent with restoration of opposite short Step-3 exits. No parameter, threshold, timeframe, stop, cost, or map rule changed.

## Scientific conclusion

The correction is valid and the original long-only artifacts must be treated as superseded. The remaining positive NQ-proxy evidence is exploratory because candidate direction was examined after phase-one results and every date-block interval crosses zero. Actual NQ futures replication and mechanism controls are required before any promotion decision.

This is an independent analytical and programmatic pass within the same AI work session, not an external human, broker, exchange, or production-readiness audit.
