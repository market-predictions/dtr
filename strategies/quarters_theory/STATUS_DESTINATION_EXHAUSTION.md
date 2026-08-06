# Quarter Destination and Exhaustion Status

Date: 2026-08-07  
Work package: `QT-WP-20260807-04`  
State: `COMPLETE_MECHANISM_REJECTED_ASSURANCE_PASS`

## Binding decision

`REJECT_DESTINATION_EXHAUSTION_MECHANISM`

The materially different destination/exhaustion hypothesis was tested across the complete registered ten-pair Dukascopy FX Cache universe and did not pass.

## Primary evidence

- A1 independent trend-leg endpoints: 272,065.
- A1 combined canonical-clustering effect: +0.000136; 95% interval [-0.004515, +0.004970].
- A2 qualified destination episodes: 47,571.
- A2 combined matched target-completion effect: +0.000422; 95% interval [-0.028827, +0.024433].
- A3 qualified arrivals: 10,901.
- A3 combined matched reversal-before-extension effect: +0.009464; 95% interval [-0.085587, +0.091110].
- All three development/validation effects failed temporal stability.
- Holm-adjusted p-values: 1.0 for A1, A2 and A3.
- Independent assurance: `PASS`.

## Data protection

- Registered Dukascopy FX Cache used; no historical reacquisition.
- All 70 annual BID/ASK source partitions for 2015–2021 independently hash-verified.
- 2022–2025 remained unopened.
- Native source pip units used, avoiding JPY scaling drift.

## Authorization boundary

Closed and not authorized:

- threshold, ATR, endpoint-window, barrier, phase, pair, year or session rescue;
- pair shopping;
- holdout opening;
- execution P&L or strategy optimization;
- Pine, alerts, sizing, paper trading or deployment.

A future Quarter-related study requires genuinely new external information or a new causal mechanism, not further subdivision of the same price-only grid.

## Primary records

- `docs/DESTINATION_EXHAUSTION_PREREGISTRATION_2026-08-07.md`
- `reports/DESTINATION_EXHAUSTION_REPORT_2026-08-07.md`
- `results/2026-08-07/destination_exhaustion_summary.json`
- `results/2026-08-07/destination_exhaustion_evidence_manifest.json`
- `reviews/DESTINATION_EXHAUSTION_ASSURANCE_2026-08-07.json`
