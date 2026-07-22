# E6 Fixed-Fraction Equity and Execution-Cost Stress — 2026-07-22

## Decision

`EQUITY_COST_STRESS_COMPLETE_NO_SIZING_AUTHORIZATION`

E6 remained profitable on the observed 304-trade sequence at all three tested risk levels and under all three cost assumptions. The main conclusion is not that more risk is better: 1.5% risk materially increases the likelihood and duration of deep drawdowns, while 0.5% is the most resilient tested envelope and 1.0% occupies the middle ground.

This historical study does not authorize a live risk level, leverage increase, Pine deployment or production use.

## Frozen design

- Starting capital: **$100,000**.
- Risk per trade: **0.50%, 1.00%, or 1.50% of current equity**.
- E6 signals, exits and one-open-position sequencing unchanged.
- Normal costs: one tick slippage per side plus $2.25 commission per side.
- Moderate costs: two ticks slippage per side plus the same commission.
- Severe costs: four ticks slippage per side plus the same commission.
- 20,000 ETH-date-block and 20,000 month-block resamples for each of the nine combinations.

## Actual historical path

| Risk per trade | Cost assumption | Final equity | Return | Maximum drawdown | Longest time under water |
|---|---|---:|---:|---:|---:|
| 0.50% | Normal | $126,940 | +26.9% | 4.3% | 162 days |
| 0.50% | Moderate | $123,565 | +23.6% | 4.6% | 190 days |
| 0.50% | Severe | $117,082 | +17.1% | 5.3% | 498 days |
| 1.00% | Normal | $159,185 | +59.2% | 8.4% | 190 days |
| 1.00% | Moderate | $150,839 | +50.8% | 9.0% | 190 days |
| 1.00% | Severe | $135,430 | +35.4% | 10.3% | 504 days |
| 1.50% | Normal | $197,231 | +97.2% | 12.4% | 190 days |
| 1.50% | Moderate | $181,932 | +81.9% | 13.3% | 301 days |
| 1.50% | Severe | $154,787 | +54.8% | 15.2% | 519 days |

All nine observed paths finished above the starting balance. The longest observed losing streak was seven trades. Poorer execution reduced both return and recovery speed, even when the final result stayed profitable.

## Resampled risk — normal costs

### 0.50% risk

- 5th-percentile final equity: approximately **$105,700–$107,500**.
- 95th-percentile maximum drawdown: approximately **9.3–10.8%**.
- Probability of finishing below $100,000: approximately **0.9–1.6%**.
- Probability of a 20% drawdown: effectively negligible in this sample.

### 1.00% risk

- 5th-percentile final equity: approximately **$110,500–$114,200**.
- 95th-percentile maximum drawdown: approximately **17.9–20.7%**.
- Probability of finishing below $100,000: approximately **1.0–1.8%**.
- Probability of a 20% drawdown: approximately **2.4–6.2%**.

### 1.50% risk

- 5th-percentile final equity: approximately **$114,200–$120,000**.
- 95th-percentile maximum drawdown: approximately **25.9–29.7%**.
- Probability of a 20% drawdown: approximately **20.5–33.7%**.
- Probability of a 30% drawdown: approximately **1.8–4.7%**.

## Resampled risk — severe costs

Severe execution means four ticks of slippage on entry and four ticks on exit, with commissions unchanged.

### 0.50% risk

- 5th-percentile final equity: approximately **$97,800–$98,800**.
- 95th-percentile maximum drawdown: approximately **12.0–13.5%**.
- Probability of finishing below $100,000: approximately **6.4–7.6%**.
- Probability of a 20% drawdown remained below **0.3%**.

### 1.00% risk

- 5th-percentile final equity: approximately **$94,500–$96,500**.
- 95th-percentile maximum drawdown: approximately **22.9–25.5%**.
- Probability of finishing below $100,000: approximately **7.1–8.3%**.
- Probability of a 20% drawdown: approximately **10.6–16.6%**.
- Probability of a 30% drawdown: approximately **0.6–1.5%**.

### 1.50% risk

- 5th-percentile final equity: approximately **$90,400–$93,300**.
- 95th-percentile maximum drawdown: approximately **32.8–36.1%**.
- Probability of finishing below $100,000: approximately **7.9–9.2%**.
- Probability of a 20% drawdown: approximately **45.1–54.9%**.
- Probability of a 30% drawdown: approximately **8.5–13.7%**.

## Plain-English interpretation

### 0.50%

This is the most forgiving tested setting. Growth is slower, but the strategy is much more likely to remain psychologically and financially manageable when the trade order is worse than the historical order or execution costs increase.

### 1.00%

This is the middle setting. The actual historical path looked good, but the resampling shows that a 20% drawdown is plausible when execution is poor. It should not be mistaken for a low-risk setting merely because the observed historical drawdown was 8.4%.

### 1.50%

This is an aggressive setting. The observed return is high, but the tail risk rises sharply. Under severe execution, roughly half of the resampled paths reached a 20% drawdown and around one in ten reached a 30% drawdown. The historical growth does not compensate for this risk for a cautious-balanced mandate.

## Strategic conclusion

E6 remains cost-robust in the sense that its observed expectancy stays positive under four ticks of slippage per side. However, execution quality matters materially: severe costs reduce the E6 expectancy from 0.161R to 0.108R and make recovery periods substantially longer.

The evidence supports carrying **0.50% and 1.00%** as paper-research risk envelopes. It argues against treating **1.50%** as a balanced default. This is a research classification, not a live sizing instruction.

## Independent review and determinism

- Exact 304-trade E6 regression reproduced.
- All cost adjustments and nine historical paths independently reconstructed.
- Independent 10,000-run date-block and month-block simulations used different seeds and confirmed the same conclusions.
- A complete repeat of the primary run produced nine of nine byte-identical artifacts.

## Next step

The frozen E6 advanced historical programme is now substantially complete. The highest-value next evidence remains either qualified fresh 2026 NQ data, materially longer contract-audited NQ history, or unchanged ES replication.

No further risk optimization, dynamic sizing, drawdown throttling or Kelly sizing should be performed on the 2023–2025 sample.
