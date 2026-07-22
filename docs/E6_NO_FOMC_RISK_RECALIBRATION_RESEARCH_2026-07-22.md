# E6 No-FOMC Risk Recalibration — 2026-07-22

## Decision

`NO_FOMC_RISK_RECALIBRATION_COMPLETE_NO_SIZING_AUTHORIZATION`

The new `E6_NO_FOMC_DAY` baseline improves the historical growth profile relative to original E6, while leaving the practical risk conclusion unchanged: 0.50% is the most resilient tested envelope, 1.00% is the middle paper-research envelope, and 1.50% remains aggressive.

## Frozen design

- Starting capital: $100,000.
- Current-equity compounding.
- 291 exact re-sequenced no-FOMC trades.
- Risk per trade: 0.50%, 1.00%, and 1.50%.
- Normal costs: one tick slippage per side plus $2.25 commission per side.
- Moderate costs: two ticks per side plus the same commission.
- Severe costs: four ticks per side plus the same commission.
- 20,000 ETH-date-block and 20,000 month-block resamples per combination.

## Historical account paths

| Risk | Normal final equity | Max DD | Moderate final equity | Max DD | Severe final equity | Max DD |
|---|---:|---:|---:|---:|---:|---:|
| 0.50% | $129,885 | 4.51% | $126,639 | 4.71% | $120,388 | 5.10% |
| 1.00% | $166,725 | 8.87% | $158,503 | 9.25% | $143,251 | 10.01% |
| 1.50% | $211,540 | 13.09% | $196,098 | 13.64% | $168,498 | 14.73% |

All nine historical paths finished above starting capital. The longest losing streak remained seven trades.

## Resampled risk — normal costs

- **0.50%:** 95th-percentile maximum drawdown approximately 8.8–9.8%; probability of finishing below starting capital approximately 0.6–0.7%; 20% drawdown effectively absent.
- **1.00%:** 95th-percentile maximum drawdown approximately 16.9–18.8%; probability of finishing below starting capital approximately 0.6–0.8%; probability of 20% drawdown approximately 1.5–3.4%.
- **1.50%:** 95th-percentile maximum drawdown approximately 24.6–27.1%; probability of 20% drawdown approximately 16.1–24.4%; probability of 30% drawdown approximately 1.1–2.5%.

## Resampled risk — severe costs

Severe execution means four ticks of slippage on entry and four ticks on exit, with commissions unchanged.

- **0.50%:** 95th-percentile maximum drawdown approximately 11.1–12.0%; probability of finishing below starting capital approximately 3.7–4.1%; probability of 20% drawdown below 0.1%.
- **1.00%:** 95th-percentile maximum drawdown approximately 21.3–22.8%; probability of finishing below starting capital approximately 4.2–4.7%; probability of 20% drawdown approximately 7.1–10.1%; probability of 30% drawdown approximately 0.3–0.7%.
- **1.50%:** 95th-percentile maximum drawdown approximately 30.5–32.5%; probability of finishing below starting capital approximately 4.7–5.2%; probability of 20% drawdown approximately 36.6–42.9%; probability of 30% drawdown approximately 5.6–8.2%.

## Comparison with original E6

At normal costs:

- 0.50% final equity increased from $126,940 to $129,885.
- 1.00% final equity increased from $159,185 to $166,725.
- 1.50% final equity increased from $197,231 to $211,540.

The no-FOMC policy improves return, but does not materially reduce the observed normal-cost drawdown. Exact portfolio re-sequencing enabled one additional losing London trade and changed the equity path. Under severe costs, the no-FOMC baseline improves both final equity and observed drawdown relative to original E6.

## Plain-English conclusion

- 0.50% remains the conservative envelope.
- 1.00% remains a credible middle paper-research envelope, but a 20% drawdown remains plausible under very poor execution.
- 1.50% remains aggressive and is not a balanced default.

Independent reconstruction and deterministic repeat passed. No live sizing, leverage, Pine, or deployment authorization follows.

## ES proxy data route

Dukascopy provides the `USA500.IDX/USD` index CFD and historical candle/tick access. It does not provide an exchange-traded ES futures history. Therefore any Dukascopy replication must be labelled an S&P 500 CFD proxy study, not an ES futures validation. The proxy dataset must be qualified for historical depth, session coverage, timestamps, missing bars, spread construction, and price discontinuities before performance is inspected.
