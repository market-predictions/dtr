# Asian Sweep Staged-Exit Research Roadmap

Status: `DISCOVERY_FAILED_CLOSED`

## Completed

- froze TP1/runner contract before authoritative discovery;
- reused immutable market-entry ledger;
- implemented 50/50 midpoint-plus-runner accounting;
- tested original-stop and break-even runners;
- used actual BID/ASK execution and slippage stresses;
- completed 2015–2019 discovery and independent reconstruction.

## Decision

`FAIL_STAGED_EXIT_DISCOVERY_STOP_BEFORE_VALIDATION`

The 2020–2025 staged-exit partitions remain unopened.

## Closed paths in this programme

- changing the 50/50 split;
- moving TP2 away from the opposite Asian boundary;
- extending the runner past 11:00 Amsterdam;
- adding BE buffers, trailing stops or partial runner exits;
- selecting EURUSD, weekdays, years, directions or score buckets;
- blending stop-management variants.

## Legitimate future programmes

1. **Direct continuation triage**
   - reversal / continuation / abstain;
   - explicit continuation target rather than inverse reversal probability.

2. **Earlier staged T0–T5 reversal execution**
   - provisional entry before complete T5 confirmation;
   - cancel or reduce when confirmation fails;
   - preserve reward/risk before the reclaim consumes the move.

3. **Independent runner-horizon hypothesis**
   - only with a new preregistration and new evidence;
   - must state an economic reason for a later exit or alternative liquidity target;
   - cannot reuse 2015–2019 merely to select the best horizon.

No Pine, alerts, paper trading or deployment is authorized.
