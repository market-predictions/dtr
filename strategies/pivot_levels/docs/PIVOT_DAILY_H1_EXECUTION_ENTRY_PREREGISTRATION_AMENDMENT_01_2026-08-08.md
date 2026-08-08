# Execution Entry Preregistration — Amendment 01

Date: 2026-08-08
Study: `DFXC-20260808-008-pivot-daily-execution-entry`
Status: `PRE_OUTCOME_IMPLEMENTATION_CLARIFICATION`

This amendment operationalizes the already-frozen terms `active quote`, `continuous FX trading segment`, and endpoint availability. It does not change the signal, entry architectures, confirmation window, exit horizon, endpoint, or promotion gate.

## Active quote

A Dukascopy M1 minute is executable/active when either the BID or ASK source row has `is_active_quote != 0`, matching the activity semantics already used to construct the accepted H1 midpoint bars. BID and ASK prices from that aligned minute grid remain the executable sides.

## Immediate-entry availability

The first active minute must occur within the first 10 clock minutes of the next contiguous H1 period. Otherwise the signal is missing for the immediate architecture rather than filled on a stale carried quote.

## Continuous four-hour segment

For confirmation windows and post-entry holding periods, a four-hour interval is treated as continuous only when each of its four constituent clock-hour bins contains at least one active quote minute. This prevents weekend/holiday stale-price bridging while tolerating ordinary inactive individual minutes.

## Fixed-time exit availability

The fixed 240-minute exit uses the final active M1 quote strictly before the target timestamp. It must occur within the final 10 clock minutes before the target. Otherwise the endpoint is missing.

## Confirmation timing

Confirmation can trigger only on active minutes from signal H1 close inclusive to four hours after signal close exclusive. A discontinuous four-hour confirmation interval is missing rather than counted as a valid non-confirmation.

## 2026 boundary

No 2026 candle may be read. Therefore any 2025 signal whose confirmation or holding interval would require 2026 data is marked missing. This is intentional holdout protection, not a data defect.

Outcome inspection begins only after this amendment is committed.