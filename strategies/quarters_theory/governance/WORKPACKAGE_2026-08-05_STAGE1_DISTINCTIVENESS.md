# Work Package — QT Stage-1 Distinctiveness

**ID:** QT-WP-20260805-01  
**Status:** Complete  
**Owner:** Quarters Theory research programme  
**Claimed:** 2026-08-05  
**Completed:** 2026-08-05

## Objective

Test the least expensive, most falsifiable implication of Quarters Theory: whether canonical 250-pip Large Quarter Points produce stronger short-horizon continuation than other roundness-matched 50-pip levels.

## In scope

- private Dukascopy GBP/USD M1 bid/ask 2015-2021;
- checksum and structural audit;
- deterministic level and crossing engine;
- 5-minute through one-day event outcomes;
- development/internal-validation split;
- weekly-block inference;
- reset, overshoot and spread sensitivities;
- compact reproducible result package.

## Out of scope

- 2022-2025 outcome analysis;
- C1/C2/C3/R1 P&L;
- trend, session, candle, macro or regime filters;
- parameter optimization;
- claims about all currency pairs.

## Acceptance criteria

- all synthetic tests pass;
- annual checksums and row counts pass;
- no duplicate timestamps, non-positive timestamp deltas or negative active spreads;
- primary and sensitivity estimates are reproducible from a frozen event ledger;
- negative findings are reported without strategy rescue attempts.

## Result

All acceptance criteria passed. The canonical 60-minute effect was -0.78 pip with a 95% year-preserving weekly-block interval of -2.58 to +1.20 pips. Gate 0 was not passed.
