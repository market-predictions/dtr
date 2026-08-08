# Implementation Validation — Daily S1/R1 × H1 Time/Weekday Study

Date: 2026-08-08
Study: `DFXC-20260808-007-pivot-daily-time-weekday`
Role: `implementation_operations`
Status: `IMPLEMENTATION_VALIDATION_PASS_ASSURANCE_PENDING`

This document is implementation-side validation only. It is not independent `governance_release_assurance`.

## Data and cache integrity

- Canonical dataset: **Dukascopy FX Cash** / `dukascopy_fx_cash_m1_bid_ask_v1`.
- Ten canonical pairs used: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Historical data came from the permanent registered cache; no historical reacquisition occurred.
- Outcome window: 2015–2025. 2026 was not used.

## Exact recent-sample reproduction

A full-history H1 reconstruction was built independently of the earlier 2022–2025 event extraction. Restricting the rebuilt 2015–2025 event ledger back to 2022–2025 reproduced the earlier time-study event population exactly:

- event count: 65,135 / 65,135;
- group counts: S1/R1 outer 33,937; S1/R1 core 24,522; S2/R2 core 6,676;
- event keys `(pair, timestamp, side, group, level)`: exact match;
- normalized pivot distance: exact match;
- wick fraction: exact match;
- lagged ATR24: exact match;
- FWD1/FWD2/FWD4/FWD8 values and missingness: exact match;
- MFE4/MAE4/excursion-asymmetry values and missingness: exact match.

This validates the vectorized full-history implementation against the separately constructed recent-sample implementation.

## Forward-continuity validation

The preregistration amendment requires contiguous UTC H1 bars. Weekend, holiday and data-gap jumps are not bridged. Forward endpoints become missing when continuity breaks before the endpoint.

## Session validation

Session phase is assigned from the signal H1 candle interval using IANA local timezones:

- Tokyo 09:00/10:00/11:00 `Asia/Tokyo`;
- London 08:00/09:00/10:00 `Europe/London`;
- New York FX 08:00/09:00/10:00 `America/New_York`.

DST changes are therefore handled by timezone conversion, not fixed UTC offsets.

Weekday is derived from the NY17 FX trading date.

## Statistical validation

Primary session-phase inference:

- endpoint: direction-adjusted FWD4 return / lagged H1 ATR24;
- cluster unit: pair-year;
- 5,000 cluster-bootstrap draws for each phase-versus-non-transition contrast;
- Holm correction across nine frozen phase comparisons;
- cluster-robust omnibus regression used as a companion global heterogeneity check.

Primary outcome:

- phase omnibus p≈0.3302;
- no individual phase survives Holm correction;
- weekday omnibus p≈0.5472.

The full-history causal baseline is also non-positive: S1/R1 core strong-wick mean FWD4 = −0.0093 ATR, clustered-bootstrap 95% CI approximately [−0.0234,+0.0050].

## Overlap sensitivity

A deterministic 4H cooldown within `(pair, side, group)` retained the first signal and suppressed following same-side/group signals for four hours, matching the primary horizon.

- total events: 180,010 → 123,696;
- S1/R1 core: 68,118 → 44,758;
- phase omnibus p≈0.3189;
- weekday omnibus p≈0.8360.

The scientific conclusion is unchanged.

## Decision validation

The evidence supports:

`NO_MATERIAL_DIRECTIONAL_TIME_OR_WEEKDAY_EDGE_TIME_MAINLY_MODULATES_MOVEMENT_MAGNITUDE`

Time materially changes MFE/MAE path amplitude, but this effect appears in controls and does not establish a directional S1/R1 timing premium.

No session-hour, weekday, session×weekday, Pine, alert, sizing or live-trading action is authorized by this implementation validation.
