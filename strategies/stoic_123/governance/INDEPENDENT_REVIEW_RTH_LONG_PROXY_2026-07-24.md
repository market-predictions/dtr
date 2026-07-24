# Independent Review — RTH Long Proxy Validation

Date: 2026-07-24
Work package: `STOIC123-WP-20260724-04`
Reviewed workflow: `30055431023`
Artifact SHA-256: `fd8efe72387c194cc49fe9734bea38ba9e65cde66c96bdaa1b679e8dd7af67e6`
Verdict: `APPROVE_REJECTION_CLOSE_RTH_LONG_HYPOTHESIS`

## Provenance and source review

The independent pass confirmed:

- phase-one configuration SHA-256 remained `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`;
- design SHA-256 was `878eb953334416006dbd7d850cfec9d4da3c3a2af91703253056b6d59d3e3ccf`;
- 2012, 2013 and 2014 files matched their frozen compressed-file checksums;
- fresh-history rows totalled 286,705 and holdout rows totalled 316,579;
- duplicate timestamps were zero;
- 2012 began on January 19 and this partial-year limitation remained explicit;
- raw source files were absent from the published result artifact;
- source classification remained Dukascopy USATECH bid-CFD proxy, not CME NQ futures.

## Ledger reconstruction

All 22 published scenario ledgers were independently reconstructed from their trade rows:

- trade counts matched;
- net R matched to floating-point tolerance;
- expectancy matched;
- maximum drawdown matched using an equity curve initialized at zero;
- every initial risk was positive;
- signal, entry and exit chronology was valid;
- no overlapping positions were found;
- all candidate and stress ledgers contained only long trades.

## Session review

Twelve non-delayed RTH or overnight entry-event files were independently classified after converting UTC signals to `America/New_York`:

- invalid RTH/overnight classifications: `0`;
- the 09:30 boundary was included;
- the 16:00 boundary was excluded;
- daylight-saving changes were handled by the IANA timezone database.

Delayed-entry scenarios were not required to remain inside RTH because the frozen rule filters signal generation and intentionally delays execution afterward.

## Management review

Both-direction technical management was retained:

- fresh history: 104 management events, comprising 66 long and 38 short signals;
- holdout: 148 events, comprising 88 long and 60 short signals.

This confirms that restricting entries to long RTH signals did not disable opposite-direction technical exits.

## Gate reconstruction

All seventeen decision gates were independently recomputed. The workflow outcome reproduced exactly:

- two gates passed;
- fifteen gates failed.

The only passes were the primary candidate trade-count thresholds. Both fresh-history years were negative for EMA break, the holdout expectancy and its two-tick stress were negative, the holdout date-block interval was entirely below zero, and both matched-time candidate comparisons failed.

The full sequence was more negative than EMA-break-only by `0.140R` expectancy on fresh history and `0.029R` on holdout. The incremental-mechanism gate was therefore correctly rejected.

## Interpretation review

RTH filtering reduced the magnitude of losses for the full-sequence comparator relative to full-session or overnight entries. It did not turn the strategy positive. This distinction is important: a useful risk attribution is not evidence of tradable alpha.

The earlier positive actual-NQ RTH attribution and inspected 2015-2021 proxy subset did not transfer to fresh 2012-2014 proxy evidence. Further subdivision of the session or tuning of related parameters would be repeated hypothesis mining.

## Final verdict

`APPROVE_REJECTION_CLOSE_RTH_LONG_HYPOTHESIS`

The evidence supports rejecting both the RTH EMA-break primary and the full RTH 1-2-3 secondary. Actual-NQ futures validation is not justified for this formulation. No Pine, sizing, alerts, paper deployment or live-trading authorization follows.

This review is an independent analytical and programmatic reconstruction within the same AI work session. It is not an external human, broker, exchange, licensing, legal or production-readiness audit.
