# Stacey Burke FX Research Status

Date: 2026-07-25  
Version: `v0.3.0-gate-b-rejection`  
Completed work packages: `SB-WP-20260724-01`, `SB-WP-20260724-02`, `SB-WP-20260725-03`  
State: `COMPLETE_REJECTED_GATE_B`

## Final decision

`FAIL_GATE_B_STOP_STACEY_BURKE_REVERSAL_PROGRAMME`

The previous-FX-day high/low sweep-and-reclaim pattern was frequent but did not demonstrate a positive control-adjusted 60-minute reversal effect on 2015–2021.

## Completed evidence

- Ten-pair Dukascopy BID/ASK M1 universe qualified for 2015–2025 plus 2026 YTD.
- Annual/YTD source integrity and hashes preserved privately.
- Preregistered 2015–2021 census completed with 2,423 retained events.
- Controlled study completed with 2,393 matched events and 11,965 controls.
- All six controlled-study integrity gates passed.
- Only one of six Gate B scientific predicates passed.
- Final workflow evidence independently reconstructed exactly.

## Primary result

| Metric | Result |
|---|---:|
| Mean event outcome | `+0.000451 ATR20` |
| Mean matched-control outcome | `+0.002159 ATR20` |
| Mean effect | `-0.001709 ATR20` |
| 95% date-block interval | `[-0.010309, +0.006900] ATR20` |
| Clustered permutation p-value | `0.670733` |
| Positive pairs | `4 / 10` |
| Positive factor blocks | `1 / 4` |

## Interpretation

The tested event is descriptive rather than a validated standalone reversal mechanism. It did not outperform matched non-event minutes, and evidence was not broad across the frozen universe.

## Protected evidence

- 2022–2023 validation outcomes were not inspected.
- 2024–2025 holdout outcomes remain untouched.
- 2026 YTD remains monitoring-only.
- No strategy entries, stops, targets, costs, R multiples or P&L were calculated.

## Authorization

Authorized:

- retain and audit the source, census and controlled-study infrastructure;
- manually reproduce the frozen rejection;
- reuse generic infrastructure for a genuinely independent hypothesis.

Blocked permanently for this research family:

- Gate C validation;
- SB-1 executable construction;
- threshold, session, delay, horizon or filter optimization;
- pair/factor selection by result;
- Pine, sizing, alerts, paper deployment and live use;
- SB-2 or SB-3 as post-failure rescue variants.

See `FINAL_DECISION.md` for the complete evidence and disposition.