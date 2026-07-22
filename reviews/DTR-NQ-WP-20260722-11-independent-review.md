# Independent Review — DTR-NQ-WP-20260722-11

## Verdict

`PASS`

The reviewer independently reconstructed the E6 advanced Blocks 0–3 evidence from the generated trade and signal tables.

## Checks passed

- registered NQ archive SHA-256 matched;
- 477-trade unfiltered control reproduced exactly;
- 304-trade E6 baseline reproduced exactly;
- all candidate metrics and two-/four-tick-each-side cost stresses reconstructed;
- completed D1 and weekly context timestamps were causal;
- path ordering satisfied sweep ≤ reclaim ≤ BOS ≤ entry;
- every executed candidate trade satisfied its frozen mask;
- all common-trade P&L matched exactly;
- all removed and replacement trades were attributed;
- no portfolio contained overlapping positions;
- independent date-block bootstraps with seed 20260723 found negative observed incremental return for every candidate and intervals crossing zero;
- the preregistered E6 mechanism classification reconstructed as `SUPPORTED`;
- the frozen candidate classifications reconstructed exactly;
- no candidate qualified as `FRESH_OOS_CHALLENGER`.

## Independent incremental intervals

| Candidate | Delta R | 95% interval | Probability positive |
|---|---:|---:|---:|
| P1 | −25.15 | [−61.70, +10.73] | 9.0% |
| P2 | −12.43 | [−35.36, +9.70] | 13.6% |
| P3 | −10.69 | [−35.34, +12.37] | 18.6% |
| R1 | −24.93 | [−61.58, +10.63] | 8.5% |
| R2 | −32.37 | [−73.01, +8.69] | 6.0% |
| I1 | −31.57 | [−70.05, +6.27] | 5.0% |

## Review conclusion

The primary interpretation is supported. E6 removes a consistently weaker cohort, while the new path-quality and reward-space filters do not improve E6 at portfolio level. Publication may proceed with decision `RETAIN_E6_NO_NEW_FILTER_ADVANCE_TO_SEQUENCING`.
