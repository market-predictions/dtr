# Dukascopy FX Cash — Research Index

Canonical machine source: `research_registry/dukascopy_fx_cash/index.json`.

Registered studies: **11**.

| Study ID | Date | Family | Question / title | Disposition | Holdout | Assurance | Source |
|---|---|---|---|---|---|---|---|
| `DFXC-20260805-001-quarters-stage1` | 2026-08-05 | quarters_theory | Quarters Theory Stage-1 distinctiveness — GBPUSD | `REJECT_MECHANISM` | `UNOPENED` | `SOURCE_RECORD_PRESENT` | `agent/quarters-theory-stage1` @ `a1ed9e50` |
| `DFXC-20260806-001-quarters-ten-pair` | 2026-08-06 | quarters_theory | Quarters Theory ten-pair Stage-1 universe confirmation | `REJECT_MECHANISM` | `UNOPENED` | `ARITHMETIC_AUDIT_RECORDED` | `agent/quarters-theory-universe` @ `3dfb4d36` |
| `DFXC-20260807-001-pivot-target-reversal` | 2026-08-07 | pivot_levels | Classic pivot levels — target, stall and reversal falsification | `REJECT_MECHANISM` | `UNOPENED` | `PASS` | `agent/pivot-level-target-reversal` @ `22c8192f` |
| `DFXC-20260807-002-pivot-spatial-zone` | 2026-08-07 | pivot_levels | Classic pivot spatial-zone follow-up | `PROMOTE_TO_HOLDOUT_CONFIRMATION` | `UNOPENED` | `PASS` | `agent/pivot-spatial-zone-followup` @ `59515ee9` |
| `DFXC-20260808-001-pivot-multiscale-terminal` | 2026-08-08 | pivot_levels | Classic pivot zones — scale-aligned terminal-hazard test | `PROMOTE_TO_HOLDOUT_CONFIRMATION` | `UNOPENED` | `NOT_REVIEWED` | `agent/pivot-multiscale-terminal-wick` @ `edf0f06f` |
| `DFXC-20260808-002-pivot-wick-rejection` | 2026-08-08 | pivot_levels | Classic pivot zones — conditional wick-rejection interaction | `PROMOTE_TO_HOLDOUT_CONFIRMATION` | `UNOPENED` | `NOT_REVIEWED` | `agent/pivot-multiscale-terminal-wick` @ `edf0f06f` |
| `DFXC-20260808-003-pivot-daily-wick-holdout` | 2026-08-08 | pivot_levels | Daily classic-pivot × H1 wick interaction — protected holdout confirmation | `SUPPORTED_INTERNAL` | `OPENED` | `NOT_REVIEWED` | `agent/pivot-daily-holdout-weekly-zone-geometry` @ `c4aeaced` |
| `DFXC-20260808-004-pivot-weekly-h4-zone-geometry` | 2026-08-08 | pivot_levels | Weekly classic-pivot × H4 zone geometry — spacing/ATR robustness | `PROMOTE_TO_HOLDOUT_CONFIRMATION` | `UNOPENED` | `NOT_REVIEWED` | `agent/pivot-daily-holdout-weekly-zone-geometry` @ `c4aeaced` |
| `DFXC-20260808-005-pivot-fibonacci-substitution` | 2026-08-08 | pivot_levels | Fibonacci pivot formula substitution — Daily/H1 and Weekly/H4 | `SUPPORTED_INTERNAL` | `UNOPENED` | `NOT_REVIEWED` | `agent/pivot-fibonacci-formula-substitution` @ `0febc662` |
| `DFXC-20260808-006-pivot-daily-level-decomposition` | 2026-08-08 | pivot_levels | Daily classic-pivot × H1 wick — named-level decomposition | `DESCRIPTIVE_ONLY` | `OPENED` | `NOT_REVIEWED` | `agent/pivot-daily-h1-level-decomposition` @ `a73bb881` |
| `DFXC-20260808-007-pivot-daily-time-weekday` | 2026-08-08 | pivot_levels | Daily S1/R1 × H1 rejection — time-of-day and weekday heterogeneity | `REJECT_NO_INCREMENTAL_VALUE` | `NOT_APPLICABLE` | `NOT_REVIEWED` | `agent/pivot-daily-h1-time-weekday-v4` @ `3891d6c7` |

## Reading rule

The row is a locator, not the evidence. Open the study's `study.json` and `result.json` when present, then follow the frozen source commit and artifact paths for the complete preregistration, run outputs, report, code and review evidence.

## Current recovered conclusions

- **Quarters Theory:** the canonical 250-pip continuation mechanism was demoted on GBPUSD and then failed unchanged across the ten-pair universe (`0/10` positive-and-stable pairs).
- **Classic pivots — broad mechanism:** high absolute reach rates do not establish magnetism; exact pivot coordinates did not beat nearby deterministic placebos on the preregistered target/stall/reversal mechanisms.
- **Classic pivots — spatial follow-up:** broad magnet/stall/reversal claims remained rejected, but a narrower daily/weekly pivot-proximity terminal-hazard effect survived internal falsification and is eligible only for one unchanged protected-holdout confirmation.

## Search tags

Use repository search against `index.json`, `INDEX.md` or per-study `tags` for concepts such as `pivots`, `zones`, `quarters-theory`, `placebo`, `terminal-hazard`, `reversal`, `round-numbers`, or pair symbols.

## Historical migration

The registry starts with the recently recovered Quarters and pivot research because these studies exposed the memory failure this framework fixes. Other historical Dukascopy FX Cash branches are listed in `migration_candidates.json` and must be reconstructed without altering their historical decisions.
