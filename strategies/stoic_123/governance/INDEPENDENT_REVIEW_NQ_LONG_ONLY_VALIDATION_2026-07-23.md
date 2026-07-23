# Independent Review — NQ Long-Only Mechanism Validation

Date: 2026-07-23
Work package: `STOIC123-WP-20260723-02`
Reviewed workflow: `30036385787`
Artifact SHA-256: `92f747b5ae07d252abb4bb0720b3aeaab8f3ebb3264ac27310425b4918c2a6e9`
Verdict: `APPROVE_NO_PROMOTION_STOP_CURRENT_LONG_ONLY_LINE`

## Provenance review

The independent pass confirmed:

- source SHA-256 exactly matched `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`;
- phase-one YAML remained byte-identical at `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`;
- design SHA-256 was `becb765fec8c933258500c3fbd2aafca84e06f4c456ea7c96f9bf6e179633777`;
- preflight reported 1,047,382 rows and the frozen source bounds;
- raw data were removed before artifact upload.

## Ledger reconstruction

All 32 published scenario trade ledgers were independently reconstructed from their rows:

- trade count matched the scenario summary;
- net R and expectancy matched to floating-point tolerance;
- every initial risk was positive;
- signal, entry, and exit chronology was valid;
- no position overlaps were found;
- long-only scenarios contained only long trades;
- short-only scenarios contained only short trades.

All four management ledgers contained both `+1` and `-1` events, confirming that entry-direction restrictions did not disable opposite-direction technical exits.

## Gate reconstruction

All 36 numerical gate outcomes were recomputed independently from the scenario summaries and date-block inference. No discrepancy was found.

- no-map passed 4 of 9 gates;
- EMA map passed 2 of 9;
- strict close passed 4 of 9;
- EMA plus breakout passed 5 of 9;
- no arm passed the positive date-block lower-bound gate;
- no arm passed the complete numerical promotion gate.

## Matched-control review

The final veto was independently checked against the frozen contract:

- no-map met event coverage but failed to exceed matched-control p95 expectancy;
- EMA map failed both coverage and matched-p95 tests;
- strict close and EMA plus breakout exceeded matched p95, but failed the 90% event-coverage requirement;
- all four arms were correctly vetoed.

The earlier finalizer omission of the recorded coverage criterion was corrected before publication. It did not alter the already-negative numerical-gate result.

## Interpretation review

The actual NQ evidence does not confirm the proxy-derived EMA-map long-only hypothesis. Positive descriptive results in no-map and EMA-plus-breakout are chronologically unstable, statistically uncertain, and fail predeclared promotion gates. Strict close adds negligible expectancy over a simple EMA break. Further same-sample filtering or directional selection would be post-hoc optimization.

## Final verdict

`APPROVE_NO_PROMOTION_STOP_CURRENT_LONG_ONLY_LINE`

The evidence package supports stopping the current NQ long-only research line. The strong historical short-side/no-map observations may be retained only as hypotheses for qualified unseen or materially longer contract-audited data. No Pine, sizing, paper-deployment, alert, or live-trading authorization follows.

This review is an independent analytical and programmatic reconstruction within the same AI work session. It is not an external human, broker, exchange, legal, licensing, or production-readiness audit.
