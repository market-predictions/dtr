# Independent Review — USA500 Forward 2015+

Date: 2026-07-24  
Work package: `STOIC123-WP-20260724-06`  
Verdict: `APPROVE_REJECTION_CLOSE_CURRENT_STOIC_FAMILY`

## Reconstruction scope

A separate programmatic pass reconstructed the compact evidence without using the production summary or gate functions for the corresponding checks.

## Findings

- 45 of 45 scenario and combined ledgers reconstructed exactly.
- Trade counts, net R, expectancy and maximum drawdown matched every published summary.
- Zero invalid initial-risk observations.
- Zero chronology failures.
- Zero overlapping positions.
- Zero invalid undelayed RTH signal classifications.
- Twelve of twelve source rows matched the frozen SHA-256 and row-count contract.
- Zero duplicate timestamps in the source audit.
- Annual candidate counts, net R and expectancy reproduced for 2015 through 2026 YTD.
- Both long and short technical-management directions remained present in every partition.
- All 19 gate outcomes reproduced exactly; 6 passed and 13 failed.
- All 45 production independent-review rows reported `PASS`.
- Raw source data were absent from the compact validation artifact.

## Decision review

The primary 2015–2019 block is decisively negative:

- 177 trades;
- −57.98R;
- −0.328R expectancy;
- 61.43R maximum drawdown;
- wholly negative date-block interval;
- four of five years negative;
- negative cost and delay stresses;
- failed matched-time control.

The 2020–2022 and 2023–2025 blocks are mildly positive at baseline but statistically uncertain and cost-sensitive. Combined 2015–2025 remains negative at −44.31R and −0.097R expectancy.

The positive 2026 YTD monitoring result is based on 29 trades, has a wide uncertainty interval and was correctly excluded from the gates.

## Verdict

`APPROVE_REJECTION_CLOSE_CURRENT_STOIC_FAMILY`

The evidence supports `REJECT_USA500_RTH_FULL_123_FORWARD_FAILURE`. No further tuning, actual-ES acquisition, Pine port, paper deployment or live-use work is justified for this mechanical formulation.

This is a same-session programmatic reconstruction, not an external financial audit.
