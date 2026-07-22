# NQ versus USA500 Parallel Replication — 2026-07-22

## Decision

`PARTIAL_COST_FRAGILE_REPLICATION`

The parallel framework successfully reproduced the frozen NQ E6 and E6-no-FOMC baselines exactly and applied the same market logic to the qualified Dukascopy USA500 bid-CFD proxy over the identical Eastern Time period.

The USA500 proxy result was positive under the normal one-tick-per-side execution assumption, but the edge was materially weaker than NQ and became slightly negative at two ticks per side. This supports only partial directional transfer, not robust ES validation.

## Framework contract

- Common period: 2022-12-26 18:00 ET through 2025-12-10 23:58 ET.
- Sessions: frozen Asia, London and New York windows.
- Calendar: Tuesday–Friday.
- Arms: original E6 and E6 with no FOMC-date entries.
- One global open position per instrument.
- Same signal, entry, stop, target, time-exit and collision logic.
- Same 0.25 prior-day-ATR E6 exclusion threshold.
- No proxy-specific parameter, session or filter tuning.
- Results remain separate; no pooled NQ/USA500 portfolio was constructed.

## Primary results

| Instrument | Arm | Trades | Net R | Expectancy | Profit factor | Max DD | Return/DD | 2-tick expectancy |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| NQ | E6 | 304 | 48.94R | 0.161R | 1.34 | 8.63R | 5.67 | 0.143R |
| NQ | E6 no-FOMC | 291 | 53.48R | 0.184R | 1.40 | 9.15R | 5.84 | 0.166R |
| USA500 proxy | E6 | 281 | 13.33R | 0.047R | 1.09 | 17.38R | 0.77 | -0.012R |
| USA500 proxy | E6 no-FOMC | 268 | 12.98R | 0.048R | 1.10 | 16.30R | 0.80 | -0.011R |

The opportunity rate was similar: 18.25 NQ E6 trades versus 19.25 proxy E6 trades per 100 eligible session opportunities. The difference was trade quality rather than a lack of signals.

## Statistical uncertainty

Date-block resampling produced:

- NQ E6: 95% expectancy interval approximately 0.020R to 0.304R; 98.7% positive probability.
- NQ E6 no-FOMC: approximately 0.038R to 0.331R; 99.4% positive probability.
- USA500 E6: approximately -0.097R to 0.197R; 73.4% positive probability.
- USA500 E6 no-FOMC: approximately -0.098R to 0.199R; 73.7% positive probability.

The proxy intervals cross zero broadly. The observed positive result is therefore weak evidence, not a confirmed transferable edge.

## Session attribution

The proxy result was concentrated in London:

| Proxy E6 session | Trades | Net R | Expectancy |
|---|---:|---:|---:|
| Asia | 67 | -7.23R | -0.108R |
| London | 107 | +31.13R | +0.291R |
| New York | 107 | -10.57R | -0.099R |

This concentration explains the positive aggregate result. It does not authorize a London-only proxy strategy or a session retune. All three frozen sessions remain in the framework.

The London proxy result was positive in 2023 and 2024 but negative in 2025. The overall proxy result was +3.04R in 2023, +11.75R in 2024 and only +0.59R in 2025.

## FOMC policy transfer

On NQ, the no-FOMC policy improved the exact re-sequenced portfolio by +4.55R.

On the USA500 proxy:

- 14 original E6 trades were removed;
- one later trade was enabled after re-sequencing;
- removed trades totalled -0.68R;
- the newly enabled trade lost -1.03R;
- the net policy effect was -0.35R.

The no-FOMC policy therefore did not improve total proxy return, although it reduced drawdown modestly. The policy remains the user-authorized NQ working baseline; this proxy result does not justify extending or redefining the event rule.

## Data and execution limitations

- USA500 is a Dukascopy bid-CFD proxy, not CME ES futures.
- The proxy uses synthetic ES-equivalent economics: 0.25-point increments, $50 point value and $2.25 commission per side.
- Historical ask prices and observed spread were unavailable.
- Dukascopy volume is not CME centralized volume.
- The proxy contains no ES contract roll behavior.
- The proxy session-range adapter requires at least 95% active-minute coverage.
- Short quote absences up to five minutes are treated as inactive quotation intervals; larger unscheduled gaps reset state and can trigger causal liquidation.

## Verification

- NQ E6 regression: exact pass.
- NQ E6 no-FOMC regression: exact pass.
- Source checksums: exact.
- No overlapping positions in any of the four trade streams.
- Cost-stress calculations independently reconstructed.
- FOMC changed-trade attribution independently reconstructed.
- Independent 10,000-run date-block bootstrap confirmed the classification.
- Complete repeat produced byte-identical comparable artifacts.

## Strategic conclusion

The framework is now suitable for continued NQ-versus-S&P-proxy comparisons without mixing data or tuning by instrument. The initial result suggests that the reversal concept is not purely NQ-specific, but its S&P transfer is weak, London-concentrated and unable to survive a modest two-tick execution assumption.

Do not promote the proxy into a second tradable baseline. The next stronger evidence would be materially longer USA500 proxy history using the unchanged framework, followed by actual contract-audited ES futures data if acquired.
