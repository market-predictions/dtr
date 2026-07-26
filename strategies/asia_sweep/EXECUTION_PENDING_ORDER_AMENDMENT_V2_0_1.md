# Asian Sweep Execution Pending-Order Amendment v2.0.1

Date frozen: `2026-07-26`  
Applies to: `EXECUTION_RESEARCH_CONTRACT_V2_0.md`

## Reason

The base contract fixed one filled trade per pair per Amsterdam date but did not explicitly define how an unfilled post-T5 limit order behaves when a later eligible same-pair event arrives before 10:00.

This amendment is frozen before any execution P&L inspection.

## Binding rule

For limit-entry variants:

1. at most one pending order may exist per pair;
2. an eligible T5 event places its order immediately after the T5 bar closes;
3. if the order fills, the daily lockout begins and later same-pair events are ignored;
4. if a later eligible T5 event occurs before the order fills, the earlier order is cancelled immediately before the later order becomes active;
5. if no later event occurs, the pending order expires at 10:00 Europe/Amsterdam;
6. a cancelled or expired unfilled order does not consume the one-trade-per-day allowance.

The simulator therefore searches each order only until the earlier of:

- the first actionable timestamp of the next eligible event in that pair/date;
- 10:00 Amsterdam.

## Tie rule

When two eligible events share the same actionable timestamp, event ID ascending determines which order is activated first; the second event immediately replaces it before either may use that timestamp for a fill. This is conservative and deterministic.

## Prohibition

Multiple simultaneous pending orders, hindsight selection of the order that later fills best, and retrospective same-day ranking are prohibited.
