# DTR-FX v0.1 cross-implementation review

Date: 2026-07-23

Decision: `NO_ARM_PASSES_DTR_FX_V01_PROMOTION`

## Scope

Two independently implemented GBPUSD DTR-FX v0.1 research paths were compared after both completed their own deterministic and arithmetic review gates. Both used the private Dukascopy GBPUSD one-minute bid/ask archive for 2022-2025, London-local session semantics, actual bid/ask execution, explicit spread/slippage/commission, and chronological development/confirmation/locked partitions.

The implementations differ in exact candidate-density and execution-contract details. Their absolute trade counts and returns are therefore not interchangeable. The comparison is used only to identify conclusions that survive both implementations; the more favorable result is not selected.

## Shared result

Both implementations independently concluded:

1. No tested arm passes the complete promotion gate.
2. `FX_B1_PREVDAY_LONDON_BOS_MID` is the strongest coherent mechanism.
3. B1 has positive full-period gross and net expectancy under the tested base costs.
4. B1 is negative in the locked 2025 partition.
5. B1 uncertainty intervals cross zero.
6. The New York arms do not provide a viable baseline.
7. No short-only, weekday, event, threshold, Pine, sizing, or deployment promotion is authorized.

## B1 comparison

| Implementation | Trades | Net R | Net expectancy | Gross expectancy | PF | 1.5x-cost expectancy | Locked 2025 expectancy |
|---|---:|---:|---:|---:|---:|---:|---:|
| A — branch implementation | 55 | 9.6862 | 0.1761R | 0.2549R | 1.424 | 0.1295R | -0.0385R |
| B — clean-room replication | 144 | 13.7980 | 0.0958R | 0.1760R | 1.180 | 0.0477R | -0.2464R |

Implementation B annual B1 results were +15.63R in 2022, -4.42R in 2023, +12.94R in 2024, and -10.35R in 2025. Implementation A also reported a negative locked 2025 outcome. Both date-block confidence intervals include zero.

## Conservative interpretation

The robust evidence is mechanism-level, not parameter-level:

- mapping London trades to previous-day high/low liquidity is more coherent than directly transferring the index-futures session map;
- targeting previous-day equilibrium/midpoint is more plausible than the tested Asian-midpoint and New York alternatives;
- the observed edge is not stable enough for promotion because locked 2025 is negative and uncertainty remains broad;
- selecting implementation A because it reports the larger expectancy would constitute model-selection bias.

## Verification

Implementation A:

- deterministic repeat: pass;
- independent arithmetic, geometry, sequencing, and aggregate-metric reconstruction: pass;
- maximum P&L reconstruction difference below 8e-13R.

Implementation B:

- 1,010 trades across six ledgers independently reconstructed;
- zero position overlap;
- zero path, cost-gate, or stop/target-precedence errors after integer-pipette normalization;
- aggregate and partition metrics reproduced within floating-point tolerance.

These are independent programmatic reviews performed in the same AI research session, not external human, broker, exchange, or legal audits.

## Next evidence gate

1. Consolidate both implementations into one exact B1 signal/execution contract and reconcile trade identities on 2022-2025 without selecting by return.
2. Freeze that contract before older-history inspection.
3. Test B1 unchanged on older GBPUSD bid/ask history, preferably 2015-2021.
4. Preserve 2026 onward as prospective evidence.
5. Stop the GBPUSD line if older-history expectancy is non-positive, cost-fragile, or concentrated in one subperiod.

No Pine implementation, position sizing, or deployment is authorized.