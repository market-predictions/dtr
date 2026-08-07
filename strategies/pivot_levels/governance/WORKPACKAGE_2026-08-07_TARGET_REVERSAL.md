# Work Package — Pivot Target / Stall / Reversal Research

- **ID:** `PIV-WP-20260807-01`
- **Status:** Active
- **Branch:** `agent/pivot-level-target-reversal`
- **Implementation role:** `implementation_operations`
- **Assurance role:** `governance_release_assurance`

## Objective

Determine whether daily, weekly, monthly, quarterly and yearly classic floor pivot levels provide distinctive target, containment/stall, trend-terminal or reversal information versus nearby placebo price coordinates.

## Explicit scope

- Daily and weekly: `S3/S2/S1/PP/R1/R2/R3`.
- Monthly, quarterly, yearly: the same principal levels plus all six adjacent arithmetic pivot midlevels.
- Registered Dukascopy FX Cache only.
- Development 2015–2019 where prior-period construction is possible; validation 2020–2021.
- 2022–2025 holdout remains unopened.

## Acceptance criteria

1. Frozen preregistration exists before outcomes.
2. All 2015–2021 source partitions actually used are checksum verified.
3. Pivot period construction is causal and New York 17:00 DST-safe.
4. Exact classic floor formulas and midlevels match preregistration.
5. P0 touch census and P1–P4 mechanism tests are produced for all five timeframes where sample exists.
6. Tolerance-zone logic explicitly permits sideways rotation before reversal.
7. Nearby placebo controls are created deterministically before outcomes.
8. 5,000 pair-year-week bootstrap and Holm family correction are applied to primary hypotheses.
9. Pair breadth and leave-one-pair-out stability are reported.
10. Separate assurance recomputes key results without modifying the candidate.
11. Status, roadmap/changelog, evidence hashes and handover are updated.

## Non-scope

No formula shopping, pivot-method variants, session/pair/year rescue, parameter tuning, 2022–2025 opening, P&L, Pine, alerts, sizing or deployment.

## Definition of done

The complete five-timeframe mechanism decision is frozen, independently assured and recorded with reproducible evidence, or a genuine data/computational blocker is documented.