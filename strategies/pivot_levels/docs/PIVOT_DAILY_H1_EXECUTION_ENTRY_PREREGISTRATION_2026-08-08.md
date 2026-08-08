# Daily S1/R1 × H1 Rejection — Executable Entry Architecture Preregistration

Date: 2026-08-08
Study ID: `DFXC-20260808-008-pivot-daily-execution-entry`
Status at creation: `PREREGISTERED_BEFORE_EXECUTION_OUTCOME_INSPECTION`
Parent: `DFXC-20260808-007-pivot-daily-time-weekday`

## Decision problem

The prior causal forward-return study showed that Daily S1/R1 proximity plus a strong directional H1 rejection wick is structurally meaningful but does not, by itself, produce positive mean reversal return when entered mechanically at the next H1 midpoint open. The next question is whether an observable confirmation entry converts that state into a tradable executable edge after real Dukascopy BID/ASK spread.

This study isolates **entry mechanics**. It does not optimize stop distance, target distance, session filters, weekday filters, pivot width, wick threshold, or indicator combinations.

## Frozen signal

- Universe: EURUSD, GBPUSD, USDCHF, AUDUSD, NZDUSD, USDCAD, USDJPY, EURJPY, GBPJPY, EURGBP.
- Source: permanent private **Dukascopy FX Cash** cache, M1 BID and ASK.
- Structural signal timeframe: H1.
- Pivot geometry: classic Daily pivots with existing NY17 FX trading-day semantics.
- Eligible named pivots: S1 and R1 only.
- Core proximity: unchanged normalized adjacent-pivot distance `d < 0.20`.
- Strong directional rejection wick: unchanged directional wick fraction `>= 0.30`.
- S1 low-side rejection implies long/reversal-up direction.
- R1 high-side rejection implies short/reversal-down direction.
- Signal becomes observable only after the complete H1 rejection candle closes.
- Signal definitions may not be retuned in this study.

## Data partitions and holdout discipline

- Development: 2015-01-01 through 2019-12-31.
- Internal validation: 2020-01-01 through 2021-12-31.
- Related exposed stability sample: 2022-01-01 through 2025-12-31.
- **Reserved fresh confirmation:** 2026 YTD ending exclusive 2026-07-24.

The 2026 YTD partition must remain unopened for performance inspection throughout this entry-architecture study. It is reserved for later confirmation only after entry plus exit/invalidation rules have been completely frozen. Merely passing this entry study does not authorize opening 2026.

## Executable price semantics

All entry and exit prices use Dukascopy BID/ASK M1 candles.

### Long trades

- Buy entries execute on ASK.
- Fixed-time exits execute by selling on BID.

### Short trades

- Sell entries execute on BID.
- Fixed-time exits execute by buying on ASK.

This embeds the observed quoted spread. No commission is added. Additional slippage is set to zero for this first entry-isolation study, except that stop-style confirmation gaps are filled conservatively at the worse of trigger price and executable minute open.

Raw candles remain private and are not committed.

## Entry architecture A — immediate executable entry

After the rejection H1 closes:

- require the next clock H1 period to be contiguous with the signal H1;
- use the first active M1 quote at or after the new H1 period begins;
- long: enter at ASK open;
- short: enter at BID open.

If no active executable quote exists in the next H1 period, the signal is ineligible for architecture A.

## Entry architecture B — rejection-candle confirmation

After the rejection H1 closes, allow a confirmation window covering the **next four contiguous clock hours**.

- S1 / long: confirmation occurs when ASK high first reaches or exceeds the completed rejection H1 midpoint high.
- R1 / short: confirmation occurs when BID low first reaches or falls below the completed rejection H1 midpoint low.
- Long fill: `max(rejection_high, ASK_open)` in the first triggering M1 candle.
- Short fill: `min(rejection_low, BID_open)` in the first triggering M1 candle.
- If no confirmation occurs inside four contiguous hours, no trade is taken and strategy return for that signal is zero.
- Any market discontinuity that breaks the four-hour confirmation window invalidates confirmation eligibility; the window is not bridged across a weekend/unsafe gap.

This is a stop-style momentum/reversal confirmation architecture, not a retrospective requirement that the signal eventually worked.

## Fixed exit used to isolate entry quality

No stop-loss or profit target is optimized here.

Every entered trade is held for **240 clock minutes from its executable entry timestamp**.

- Long exits at the last active BID close at or immediately before entry timestamp + 240 minutes.
- Short exits at the last active ASK close at or immediately before entry timestamp + 240 minutes.
- The complete holding interval must remain inside a continuous FX trading segment. Weekend/unsafe discontinuities make the trade endpoint missing rather than bridged.

The fixed 4H exit exists only to compare entry architectures cleanly. It is not proposed as the eventual trading exit.

## Primary endpoint

Per-signal net executable reversal return, normalized by the frozen signal H1 lagged ATR24:

- long entered trade: `(BID_exit - ASK_entry) / ATR24`;
- short entered trade: `(BID_entry - ASK_exit) / ATR24`;
- confirmation architecture with no qualifying trigger: `0` per signal;
- signals/trades invalidated by data-continuity failure are missing, not zero.

Using zero for a valid non-confirming signal makes the confirmation architecture directly comparable to the always-enter immediate architecture as a decision rule rather than reporting only selected winning trades.

## Primary comparison and gate

Primary contrast:

`mean_per_signal_return(CONFIRMATION) - mean_per_signal_return(IMMEDIATE)`

Primary null: the confirmation architecture does not improve per-signal executable expectancy over immediate entry.

Primary alternative: confirmation produces higher per-signal executable expectancy.

Confirmation may be promoted to the next stop/target study only if all are true:

1. full 2015-2025 confirmation-minus-immediate point estimate is positive;
2. pair-year clustered bootstrap 95% CI for that difference has lower bound > 0;
3. confirmation per-signal expectancy itself is > 0 with 95% CI lower bound > 0;
4. confirmation-minus-immediate point estimate is positive in both 2015-2019 and 2020-2021;
5. no single pair contributes more than 35% of aggregate confirmation P&L-equivalent normalized return.

Failure of any gate prevents promotion of this exact confirmation rule. No threshold/window rescue is allowed on 2015-2025.

## Secondary diagnostics

Report without selection authority:

- executable expectancy of immediate entry;
- executable expectancy of confirmation entry per signal and per entered trade;
- confirmation rate;
- median/mean minutes from signal close to confirmation;
- positive-return probability;
- MFE and MAE over the 4H post-entry holding interval where safely reconstructable;
- S1 versus R1;
- pair breadth and year breadth;
- development / validation / 2022-2025 stability splits;
- session phase as descriptive execution context only, using the already-frozen Tokyo/London/New York H1/H2/H3 labels;
- weekday descriptive only.

No session or weekday selection is allowed because the parent study rejected them as stable directional filters.

## Inference

- Unit of observational clustering: pair-year.
- Bootstrap: 5,000 pair-year cluster resamples for primary mean effects/contrasts.
- The primary family contains one predeclared architecture contrast.
- Secondary diagnostics are descriptive unless explicitly stated otherwise.

## Overlap / rearm

Primary ledger retains the existing side-specific signal observations to preserve comparability with the parent causal study.

A deterministic robustness ledger will suppress a new same-pair/same-direction S1/R1 signal until four hours after the prior accepted signal close. It may confirm robustness but cannot rescue a failed primary gate.

## Controls

- Immediate executable entry is the primary causal baseline.
- Existing S2/R2 core strong-wick and S1/R1 matched outer strong-wick cohorts may be reconstructed as falsification controls if needed to determine whether any confirmation effect is pivot-specific. They are not part of the primary promotion gate.

## Prohibited rescue paths

After outcome inspection begins, do not:

- change the 30% wick threshold;
- change S1/R1 zone width;
- change the four-hour confirmation window;
- substitute candle close, midpoint, bid-only or ask-only structural signals;
- mine alternative confirmation offsets or arbitrary price buffers;
- add session/day filters;
- add trend, RSI, MA, divergence, COT, Asian-range or other conditioning variables;
- optimize stops or targets unless the confirmation architecture first passes the frozen promotion gate;
- inspect 2026 YTD performance during this phase.

## Next step if the promotion gate passes

Freeze a separate small execution-risk family for the selected confirmation entry: one structural invalidation stop and one ATR stop, paired with a small preregistered target/time-exit family. Only after that complete strategy rule is frozen may 2026 YTD be opened under a dedicated authorization record.

## Governance

This is research only. No Pine strategy, alerts, sizing, publication, automated execution or live-trading authority is created. Implementation may not self-certify. Independent `governance_release_assurance` remains required for closeout.