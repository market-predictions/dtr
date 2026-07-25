# Final Handover — Asian Sweep Ten-Pair FX Discovery

Date: 2026-07-25  
Work package: `AS-WP-20260725-10`  
Branch: `agent/asia-sweep-fx-ten-pair`  
Decision: `FAIL_DISCOVERY_STOP_BEFORE_MECHANISM_VALIDATION`

## Scope completed

A preregistered 2015–2019 mechanism study was executed on EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY and EURGBP using qualified Dukascopy BID/ASK M1 source artifacts.

The study reused the unchanged causal Asian Sweep auction-state detector and tested whether a London `REJECTION` state added 60-minute reversal value over five distinct-date matched non-rejection boundary events.

## Results

- matched rejection events: 2,498;
- matched controls: 12,490;
- independent dates: 1,104;
- mean rejection return: `+0.005890` Asian-range fractions;
- mean matched-control return: `+0.024507`;
- mean incremental effect: `-0.018617`;
- 95% date-block interval: `[-0.046224, +0.008483]`;
- one-sided clustered permutation p-value: `0.910809`;
- positive pairs: `4 / 10`;
- positive factor blocks: `1 / 4`;
- frozen gates passed: `5 / 10`.

The primary events did not add reversal value; matched non-rejection breaches reversed more.

## Independent audit

The preserved evidence was independently reconstructed and confirmed:

- unique event identities;
- exactly five controls and five distinct control dates per event;
- zero same-date leakage;
- correct pair identity;
- event, control and effect arithmetic;
- pair, factor and annual attribution;
- concentration calculations;
- all 10,000 bootstrap iterations;
- all 10,000 clustered permutation iterations;
- every frozen gate outcome.

No source, matching, arithmetic or inference defect explains the negative result.

## Protected boundaries

- 2020–2021 mechanism validation remains unopened;
- 2022–2023 executable validation remains unopened;
- 2024–2025 remains an untouched holdout;
- no executable P&L was calculated;
- no positive-pair, NZDUSD, weekday, direction, volatility or PDH/PDL-cluster rescue is authorized;
- no Pine, sizing, alert, paper-trading or deployment work is authorized.

## Repository evidence

- final decision: `strategies/asia_sweep/FINAL_DECISION_FX_TEN_PAIR.md`;
- preregistration: `strategies/asia_sweep/FX_TEN_PAIR_PREREGISTRATION.md`;
- status: `strategies/asia_sweep/STATUS_FX_TEN_PAIR.md`;
- roadmap: `strategies/asia_sweep/ROADMAP_FX_TEN_PAIR.md`;
- changelog: `strategies/asia_sweep/CHANGELOG_FX_TEN_PAIR.md`;
- workflow run: `30149721151`;
- decision artifact digest: `sha256:9f0dd7f498e5621d72629e0dba7405a554656024c46c738cb4a0499788c689cd`;
- pooled ledger SHA-256: `9f2c2c31c2a7ad2718b59bf6524b10be983402a74a0c3ef1945e3daff6451e2a`;
- decision JSON SHA-256: `c8c17fa9e1bde399c5cdbc1735c91f8395ef5ea8bcb4db3def8533ca004d71ac`.

## Final disposition

The work package and claim are closed. The heavy workflow is retained as manual reproduction only. Any future Asian-session programme must begin with a distinct economic hypothesis, new preregistration and unseen evidence; it may not be described as an optimization of this rejected formulation.
