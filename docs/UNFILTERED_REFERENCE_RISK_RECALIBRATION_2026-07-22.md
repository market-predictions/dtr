# Unfiltered Timing-Corrected Reference Risk Recalibration — 2026-07-22

## Decision

`UNFILTERED_REFERENCE_RISK_RECALIBRATION_COMPLETE_NO_SIZING_AUTHORIZATION`

The neutral 477-trade timing-corrected scientific reference is materially less resilient than the E6-based policy candidate. This confirms that all risk figures must identify the exact conditioned trade stream and must not be treated as strategy-wide sizing authorization.

## Frozen design

- Starting capital: $100,000.
- Trade stream: `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1` — 477 trades, 42.577515R net and 0.089261R expectancy.
- Current-equity risk: 0.50%, 1.00%, and 1.50% per trade.
- Execution: published one-tick-per-side returns; two-tick-per-side; four-tick-per-side.
- 20,000 session-date-block and 20,000 month-block resamples per risk/cost combination.

## Historical sequence

| Risk | Normal final equity | Normal max DD | Severe-cost final equity | Severe-cost max DD |
|---|---:|---:|---:|---:|
| 0.50% | $122,595 | 7.94% | $108,035 | 9.69% |
| 1.00% | $147,582 | 15.34% | $114,605 | 18.55% |
| 1.50% | $174,491 | 22.24% | $119,394 | 26.63% |

The historical sequence had a nine-trade maximum losing streak. At 1% normal costs, the account spent as many as 109 trades below its prior equity high.

## Resampled risk

### Normal costs

- 0.50% risk: approximately 6.1–6.5% probability of finishing below start; 95th-percentile drawdown approximately 15.9–16.3%; 20% drawdown probability approximately 1.0–1.5%.
- 1.00% risk: approximately 6.8–7.4% probability of finishing below start; 95th-percentile drawdown approximately 29.8–30.4%; 20% drawdown probability approximately 32.4–33.7%; 30% drawdown probability approximately 4.8–5.4%.
- 1.50% risk: approximately 7.7–8.4% probability of finishing below start; 95th-percentile drawdown approximately 41.8–42.5%; 20% drawdown probability approximately 77.3–77.8%; 30% drawdown probability approximately 28.1–29.4%.

### Severe four-tick-per-side costs

- 0.50% risk: approximately 28.1–28.6% probability of finishing below start; 95th-percentile drawdown approximately 21.4–21.8%; 20% drawdown probability approximately 7.3–8.0%.
- 1.00% risk: approximately 30.5–30.9% probability of finishing below start; 95th-percentile drawdown approximately 38.9–39.5%; 20% drawdown probability approximately 60.7–61.7%; 30% drawdown probability approximately 19.8–20.8%.
- 1.50% risk: approximately 33% probability of finishing below start; 95th-percentile drawdown approximately 53.0–53.7%; 20% drawdown probability above 92%; 30% drawdown probability approximately 56–57%.

## Interpretation

- The 477-trade scientific control remains positive historically, but its edge is thin and execution-sensitive.
- 1.00% risk is not a neutral or low-risk setting on this stream; resampling indicates a roughly one-in-three normal-cost probability of a 20% drawdown.
- 1.50% is clearly incompatible with a cautious-balanced mandate.
- The more favourable E6/no-FOMC risk curves are conditional on filters selected on the historical sample and cannot replace this neutral control analysis.

No live risk level, leverage, Pine implementation, or deployment action follows.
