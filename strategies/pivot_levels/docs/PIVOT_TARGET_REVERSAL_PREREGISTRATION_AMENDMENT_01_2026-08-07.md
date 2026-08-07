# Pivot Target / Reversal Preregistration Amendment 01

Date: 2026-08-07
Programme: `PIVOT-TARGET-REVERSAL-V1`
Status: frozen before any outcome/event result file was persisted.

## Operational clarification

The EURUSD dry execution produced no result/event file before its runtime limit. Profiling showed that enumerating all simultaneously eligible real and placebo levels is computationally wasteful and causally redundant.

For P2–P4, at each qualified H1 trend state and pivot timeframe:

1. identify all real pivot coordinates ahead of the trend that satisfy the preregistered approach-distance and no-prior-touch rules;
2. retain only the nearest eligible **real pivot**;
3. identify all nearby placebo coordinates ahead of the trend that satisfy the same rules;
4. retain only the nearest eligible **placebo coordinate**;
5. resolve those candidates with the frozen M15 first-passage rules.

Rationale: a farther level of the same candidate class cannot be an independent destination before price encounters a nearer coordinate. The nearest-candidate rule therefore removes overlapping pseudo-opportunities rather than selecting on outcome.

No pivot formula, timeframe, level set, midlevel, placebo geometry, tolerance zone, trend threshold, barrier, dwell window, sample boundary, bootstrap rule, multiplicity rule or promotion gate is changed.