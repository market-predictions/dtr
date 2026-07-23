# Asia Sweep Research Preregistration

## Status

`PREREGISTERED_FOUNDATION_DATA_NOT_FULLY_QUALIFIED`

## Strategy family

The declared family contains exactly four primary variants: AS-A, AS-B, AS-C and AS-D. No additional threshold variant may be promoted from the historical lockbox without being counted in the multiple-testing family.

## Instruments

NQ and ES use identical strategy parameters except tick value, point value, commission and data provenance.

## Periods

- development: 2023-01-01 through 2024-06-30;
- historical validation: 2024-07-01 through 2025-03-31;
- later historical research: 2025-04-01 through 2025-12-11;
- fresh OOS: separately sealed after a primary variant is frozen.

The latter two historical partitions are not represented as pristine OOS because the wider repository has already examined the period.

## Primary selection question

Which, if any, confirmation adds incremental value over the simple same-bar reclaim control?

## Required reporting

- NQ and ES separately;
- matched-date pooled result;
- London and New York separately;
- long and short separately;
- year, weekday and window-by-weekday concentration;
- one-, two- and four-tick stress;
- MFE, MAE, holding time and time-exit rate;
- session-date and month-block bootstrap intervals;
- paired differences versus AS-A;
- familywise-aware interpretation across the four variants.

## Promotion gate

A primary candidate must have:

1. positive expectancy in NQ;
2. positive expectancy in ES;
3. pooled expectancy at least 0.08R before extra stress;
4. positive pooled expectancy after two-tick stress;
5. profit factor at least 1.15;
6. at least 80 locked-evaluation trades per instrument;
7. no instrument contributing more than 70% of pooled net R;
8. no year contributing more than 50% of pooled net R;
9. no window-by-weekday cell contributing more than 50% of net R;
10. no unresolved roll or data-quality cluster explaining more than 20% of net R;
11. directionally stable results under plausible timestamp interpretations;
12. incremental value over AS-A;
13. familywise-aware support.

Passing this gate permits only fresh-OOS and paper research.

## Failure handling

Negative or non-robust variants remain recorded. They are not combined with DTR or with each other to rescue performance.
