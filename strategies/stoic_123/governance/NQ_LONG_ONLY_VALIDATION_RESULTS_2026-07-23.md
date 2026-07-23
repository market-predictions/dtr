# NQ Long-Only Mechanism and Futures Replication — Final Results

Date: 2026-07-23
Work package: `STOIC123-WP-20260723-02`
Decision: `NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`
Workflow run: `30036385787`
Artifact SHA-256: `92f747b5ae07d252abb4bb0720b3aeaab8f3ebb3264ac27310425b4918c2a6e9`

## Source and integrity gate

The study used the registered NQ futures research archive only after exact verification:

- source SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`;
- phase-one YAML SHA-256: `5d6909bd5740e1cdea9bd3d47a9818289a6faa8b9a61338726afdc53289ff805`;
- rows: `1,047,382`;
- first timestamp: `2022-12-26 18:00 ET`;
- last timestamp: `2025-12-10 23:58 ET`.

Raw market data were removed before artifact upload and are not committed.

## Corrected direction contract

Long-only restricts entries only. The 15-minute management detector remains two-directional, so a complete opposite short Step-3 may close a long. Every candidate management ledger contained both long and short management events.

## Primary long-only results

| Candidate | Trades | Net R | Expectancy | PF | Max DD | Return/DD | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| No-map control | 555 | +75.71 | +0.136R | 1.149 | 100.28R | 0.76 | -54.44R | +51.50R | +79.68R |
| EMA map | 252 | -1.83 | -0.007R | 0.992 | 36.63R | -0.05 | -22.61R | +8.81R | +11.96R |
| Strict close | 226 | +10.97 | +0.049R | 1.052 | 50.48R | 0.22 | +8.48R | -11.45R | +13.94R |
| EMA plus breakout | 147 | +41.56 | +0.283R | 1.302 | 44.91R | 0.93 | -40.72R | +48.87R | +33.41R |

The partial December 2022 observations are not treated as a full validation year.

## Uncertainty

Every long-only date-block 95% interval crossed zero:

- no-map: `[-0.221R, +0.526R]`;
- EMA map: `[-0.520R, +0.607R]`;
- strict close: `[-0.490R, +0.660R]`;
- EMA plus breakout: `[-0.492R, +1.215R]`.

Therefore no candidate passed the required positive lower-bound gate.

## Cost and delay robustness

- No-map remained positive at two ticks per side and with one- and five-minute delays, but failed year stability, concentration, drawdown-improvement, and uncertainty gates.
- EMA map was negative at baseline, under two-tick stress, and with a one-minute delay.
- Strict close remained slightly positive under two-tick stress and improved under delayed entries, but failed year stability, mechanism, concentration, and uncertainty gates.
- EMA plus breakout remained positive under two-tick stress and both delays, but lost `40.72R` in 2023, missed the 25% drawdown-reduction gate, and failed the uncertainty gate.

Delayed-entry improvements are descriptive execution-path effects, not authorization to optimize entry delay.

## Mechanism controls

Against the simpler EMA-break-only control:

- no-map improved expectancy by `+0.068R`, but its return-to-drawdown was materially worse;
- EMA map underperformed by `-0.070R` expectancy;
- strict close improved by only `+0.002R`, insufficient to justify the additional sequence complexity;
- EMA plus breakout improved by `+0.158R`, but remained chronologically unstable and statistically uncertain.

## Matched-time control

Fifty deterministic matched-time replicates were run per candidate without changing the frozen matching rules.

- No-map achieved 99.0% minimum event coverage, but full-sequence expectancy did not exceed the matched-control 95th percentile.
- EMA map, strict close, and EMA-plus-breakout achieved only 80.1%, 81.1%, and 67.7% minimum coverage respectively, below the frozen 90% comparability requirement.
- All four candidates were therefore vetoed by the matched-control contract.

The matching design was not broadened after returns were inspected.

## Directional finding

The actual NQ archive did not confirm the proxy-based long-only thesis. The no-map both-direction result was `+266.74R`, while its short-only component was `+188.33R` at `+0.516R` expectancy. This is a post-hoc directional observation only. It does not authorize a short-only promotion or another same-sample search.

## Promotion-gate result

Passed numerical gates out of nine:

- no-map: `4/9`;
- EMA map: `2/9`;
- strict close: `4/9`;
- EMA plus breakout: `5/9`.

No arm passed all numerical gates. All four were additionally vetoed by the matched-control contract.

## Decision

`NO_PROMOTION_STOP_NQ_LONG_ONLY_CURRENT_SAMPLE`

- Reject EMA-map long-only as the primary candidate on actual NQ futures.
- Do not promote strict close or EMA-plus-breakout.
- Do not tune sessions, delays, maps, stops, targets, timeframes, or matched-control rules on this sample.
- Do not port a candidate to Pine or authorize sizing, alerts, paper deployment, or live use.
- Preserve the observed short-side asymmetry only as a fresh-data hypothesis. It may be tested later only on qualified unseen or materially longer contract-audited data under a new preregistration.
