# Daily S1/R1 × H1 Time/Weekday Study — Preregistration Amendment 01

Date: 2026-08-08
Study: `DFXC-20260808-007-pivot-daily-time-weekday`
Status: `FROZEN_PRE_OUTCOME_FORWARD_CONTINUITY_CLARIFICATION`

This amendment is frozen before forward-return outcomes are inspected.

## Contiguous forward-horizon rule

The signal is observed at the close of H1 candle `t`. Entry reference is the open of candle `t+1` only if `timestamp[t+1] == timestamp[t] + 1 hour`.

For an `N`-hour forward endpoint, every H1 candle from `t+1` through `t+N` must be exactly one UTC clock hour after the preceding candle. If any gap occurs before the endpoint, that endpoint is missing for that signal.

This prevents weekend, holiday or data-gap jumps from being misclassified as ordinary one-, two-, four- or eight-hour session response.

The rule changes no pivot, wick, session, weekday, horizon or statistical hypothesis in the parent preregistration.
