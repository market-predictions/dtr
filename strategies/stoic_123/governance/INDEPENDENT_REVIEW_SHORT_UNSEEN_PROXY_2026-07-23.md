# Independent Review — Stoic Short-Side Unseen Proxy Falsification

Date: 2026-07-23
Work package: `STOIC123-WP-20260723-03`
Reviewed workflow: `30047912422`
Artifact SHA-256: `324849b9ae7958f13f426dc0f12763b118e2f2ffe2add827ab2a4d93ab840418`
Verdict: `APPROVE_REJECTION_CLOSE_CURRENT_STOIC_FAMILY`

## Provenance review

The independent pass confirmed:

- all eight annual/YTD source files matched their frozen checksums;
- the phase-one configuration remained byte-identical at `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`;
- design SHA-256 was `ff6c0488202f4da78148b1cc08e987e167507f8322df0eaf94a44049b031c2a9`;
- source rows totalled `1,998,563` for 2015-2021 and `189,836` for 2026 YTD;
- duplicate timestamps were zero;
- neither partition overlapped the inspected 2022-12-26 through 2025-12-10 NQ sample;
- raw source files were absent from the published artifact.

## Ledger reconstruction

All 16 scenario trade ledgers were independently reconstructed from their rows:

- trade counts matched the published summaries;
- net R and expectancy matched to floating-point tolerance;
- every initial risk was positive;
- signal, entry, and exit chronology was valid;
- no position overlaps were found;
- short-only scenarios contained only short trades;
- long-only scenarios contained only long trades;
- both-direction scenarios contained both directions.

Both management ledgers retained long and short signals:

- older history: 596 events, comprising 390 long and 206 short signals;
- forward 2026: 67 events, comprising 40 long and 27 short signals.

This confirms that restricting entry direction did not disable opposite-direction technical exits.

## Gate reconstruction

All twelve promotion gates were independently recomputed. The workflow result reproduced exactly: four passed and eight failed.

The older-history short result was `-86.13R` over 696 trades with `-0.124R` expectancy. Its date-block interval crossed zero and only two of seven years were positive. Two-tick costs and delayed entries remained negative.

The 2026 YTD short result was `+2.12R` over 43 trades, but its interval was `[-0.672R, +0.914R]`, its full sequence underperformed the simpler EMA-break control by `0.031R` expectancy, and it failed the matched-control contract.

## Matched-control review

- Older history met event-coverage and holding-period comparability, but full expectancy did not exceed matched-control p95.
- Forward 2026 met event coverage but failed holding-period comparability and matched-p95 superiority.
- Both partition-level matched-control outcomes were correctly classified as failures.

## Interpretation review

The post-hoc actual-NQ short asymmetry did not reproduce on the long unseen proxy history. The small 2026 result is statistically indeterminate and weaker than a simpler short EMA-break control. The descriptive long and both-direction comparators are also post-hoc within this artifact and cannot become new candidates.

Further filtering or retuning would be repeated hypothesis mining rather than validation.

## Final verdict

`APPROVE_REJECTION_CLOSE_CURRENT_STOIC_FAMILY`

The evidence supports rejecting the current short-side hypothesis and closing the current mechanical Stoic 1-2-3 family. Purchasing additional NQ data for this exact formulation is not justified. No Pine, sizing, paper-deployment, alert, or live-trading authorization follows.

This review is an independent analytical and programmatic reconstruction within the same AI work session. It is not an external human, broker, exchange, legal, licensing, or production-readiness audit.
