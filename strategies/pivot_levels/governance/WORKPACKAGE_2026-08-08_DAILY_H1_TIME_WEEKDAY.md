# Work Package — PIV-WP-20260808-07

Date: 2026-08-08
Study: `DFXC-20260808-007-pivot-daily-time-weekday`
Role: `implementation_operations`
Status: `IMPLEMENTATION_COMPLETE_ASSURANCE_PENDING`

## Objective

Test time-of-day and weekday as independent conditioning variables for the observable Daily S1/R1 + strong directional H1 rejection signal without post-hoc session filtering.

## Frozen design

- Daily classic S1/R1 core: normalized distance <20% of adjacent pivot spacing.
- Strong directional H1 wick: >=30% of candle range.
- Signal observed at H1 close; forward measurement from next contiguous H1 open.
- Primary endpoint: direction-adjusted FWD4 close return / lagged H1 ATR24.
- Tokyo, London and New York FX each split into Hour 1, Hour 2 and Hour 3.
- All other hours form `NON_TRANSITION` control.
- Weekday Monday–Friday uses NY17 FX trading date.
- S2/R2 core and S1/R1 outer strong-wick controls retained.
- Pair-year clustered bootstrap; Holm across nine primary phase comparisons.

## Definition of done

1. Exact cache-first data use and 2026 exclusion recorded.
2. Full 2015–2025 event ledger constructed.
3. 2022–2025 recent-sample event extraction exactly reproduced by independent full-history implementation.
4. Primary session-phase and weekday results computed.
5. Secondary FWD1/FWD2/FWD8 and MFE/MAE path-shape results reported without rescue selection.
6. Overlap/cooldown sensitivity reported.
7. Negative findings retained.
8. Study/result registry, report, claim and handover written.
9. Independent assurance pending before scientific closeout.

## Candidate decision

`NO_MATERIAL_DIRECTIONAL_TIME_OR_WEEKDAY_EDGE_TIME_MAINLY_MODULATES_MOVEMENT_MAGNITUDE`

## Interpretation boundary

This study may classify time as directional, non-directional/volatility context, or unsupported. It cannot authorize a trading filter, execution rule, Pine implementation or live trading.
