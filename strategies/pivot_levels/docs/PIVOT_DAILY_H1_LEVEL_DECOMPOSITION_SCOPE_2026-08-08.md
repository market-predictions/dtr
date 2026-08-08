# Daily/H1 Named-Level Wick Decomposition — Frozen Diagnostic Scope

Date: 2026-08-08
Study: `DFXC-20260808-006-pivot-daily-level-decomposition`
Parent: `DFXC-20260808-003-pivot-daily-wick-holdout`
Status: `FROZEN_BEFORE_LEVEL_OUTCOME_INSPECTION`

## Purpose

Decompose the confirmed Daily classic-pivot × H1 wick association by named pivot level without retuning the parent phenomenon.

The parent holdout preregistration already authorized named-level diagnostics descriptively only and prohibited named-level selection. Before inspecting the recovered named-level outcomes in this follow-up, the following primary comparison was additionally frozen in the PR #77 discussion:

- first-order tier: `S1 + R1`;
- second-order tier: `S2 + R2`;
- primary diagnostic contrast: pivot-specific wick interaction(first-order) minus pivot-specific wick interaction(second-order).

Secondary reporting:

- PP, S1, R1, S2, R2, S3, R3 individually;
- symmetric tiers S1/R1, S2/R2, S3/R3;
- weak-wick and strong-wick core/outer terminal rates;
- pair and year breadth;
- implementation-reconstruction sensitivity.

## Frozen parent definitions

No change is permitted to:

- classic daily floor-pivot formula;
- NY17 FX trading-day calendar;
- nearest-pivot assignment;
- side-specific adjacent-level spacing;
- core `0 <= d < 0.20`;
- outer `0.30 <= d <= 0.50`;
- H1 midpoint bars;
- ATR24 / 0.75 directional-change terminal concept;
- strictly-later-bar terminal confirmation;
- strong directional wick `>=30%`;
- weak directional wick `<10%`;
- ten-pair Dukascopy FX Cash universe;
- 2022-2025 consumed holdout window.

## Interpretation boundary

This is a diagnostic/mechanistic decomposition of an already consumed holdout. It is not a fresh protected-holdout confirmation and does not authorize selecting or dropping named levels for trading.

Because the original heavy terminal ledger was intentionally not retained, exact observation-population reconstruction is required first. Any named-level terminal calculation whose all-level reference materially contradicts the frozen parent result must be labeled reconstruction evidence rather than exact replay.

No post-outcome threshold tuning, pair exclusion, session filtering, level exclusion, alternate wick threshold, alternate zone width, or alternate pivot formula is permitted.
