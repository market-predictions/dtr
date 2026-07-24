# Source Qualification — RTH Long Proxy Validation

Date: 2026-07-24
Work package: `STOIC123-WP-20260724-04`
Workflow run: `30054529747`
Performance inspected: **no**

## Result

| Label | Active rows | First UTC timestamp | Last UTC timestamp | SHA-256 | Decision |
|---|---:|---|---|---|---|
| 2010 | 0 | — | — | `c75da7d42764e0d707018b67fcbe501f23220ea0c8e098bd3695c232f37f1bd8` | unavailable |
| 2011 | 1,515 | 2011-09-18 21:53 | 2011-09-23 12:57 | `ef51d7a9785673cb8d37d4cc9fb4204dd2ac1a980614f9e708af0c9056913e2e` | insufficient fragment |
| 2012 | 92,177 | 2012-01-19 16:15 | 2012-12-31 21:00 | `794af390136b1e0b03b615544d8a40d96bf50aa8018e76b0cb6f6b15f57bb27d` | partial but usable |
| 2013 | 194,528 | 2013-01-01 05:44 | 2013-12-31 21:00 | `aff83ca33342c2b8bf3c86acdab6c49eeb7a3c2dfad62864e323220f8b39e434` | qualified history |
| 2014 | 316,579 | 2014-01-02 11:00 | 2014-12-31 19:00 | `7014f3d44cf6e270ff7699b2c0ee0d254dcfe2887dc11097e8a147a6dbbc484f` | qualified holdout |

Every partition reported zero duplicate timestamps and retained the explicit classification `Dukascopy USATECH bid-CFD proxy; not CME NQ futures`.

## Frozen execution decision

- Exclude 2010 because no source exists.
- Exclude 2011 because only 1,515 active rows from one week are available.
- Use 2012 and 2013 as the fresh history partition.
- Use 2014 as a separately evaluated holdout.
- Reflect the shorter source history in source-size-appropriate gates; no performance result informed this adjustment.
- Keep 2015-2021 and 2026 as inspected exploratory data that cannot promote a candidate.

The 2012 start on January 19 and the limited two-year history are explicit limitations. Passing this proxy screen can only justify an actual-NQ futures validation.
