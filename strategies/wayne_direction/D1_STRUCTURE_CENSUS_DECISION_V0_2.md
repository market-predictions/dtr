# Wayne Direction-First D1 Structural Census — Decision v0.2

Date: 2026-07-27  
Authoritative run: `30226928816`  
Evaluated head: `e59818e036f46f490a59d1f9462f6e244ccb43eb`  
Artifact: `wayne-direction-first-census`  
Artifact digest: `sha256:910a25fd0775c6f83a0985d39a2991f9b773ccd06c77b6470ad8739cbb37286a`

## Binding census decision

`FAIL_STRUCTURE_CENSUS_REVIEW_DEFINITION`

This is a sample-sufficiency decision, not a finding that the structural sequence is invalid.

## Population

- pairs: AUDUSD, EURUSD, GBPUSD, USDCAD, USDCHF and USDJPY;
- years: 2015–2021 only;
- 10,895 validated New York 17:00 D1 bars;
- 2,863 causally confirmed swing points;
- no 2022–2025 source entered the workflow;
- no macro, seasonality, entry or execution outcome was opened.

## Complete trend-start events

| Pair | Bull | Bear | Total |
|---|---:|---:|---:|
| AUDUSD | 7 | 10 | 17 |
| EURUSD | 6 | 9 | 15 |
| GBPUSD | 9 | 6 | 15 |
| USDCAD | 9 | 3 | 12 |
| USDCHF | 11 | 6 | 17 |
| USDJPY | 4 | 3 | 7 |
| **Pooled** | **46** | **37** | **83** |

The preregistered census gate required 300 pooled confirmations and at least 40 in four pairs. No pair reached 40, so the gate failed.

## Temporal breadth

The 83 events were distributed across every development year:

| Year | Bull | Bear | Total |
|---|---:|---:|---:|
| 2015 | 5 | 4 | 9 |
| 2016 | 8 | 5 | 13 |
| 2017 | 7 | 5 | 12 |
| 2018 | 5 | 6 | 11 |
| 2019 | 11 | 5 | 16 |
| 2020 | 5 | 5 | 10 |
| 2021 | 5 | 7 | 12 |

The low count is therefore a consequence of the strict transition definition, not a single-year collapse.

## Structural funnel

Bullish:

- 197 double bottoms;
- 80 higher-high breaks of structure;
- 71 retests;
- 57 confirmed higher lows;
- 46 continuation higher highs and trend confirmations.

Bearish:

- 174 double tops;
- 73 lower-low breaks of structure;
- 61 retests;
- 49 confirmed lower highs;
- 37 continuation lower lows and trend confirmations.

Most attrition occurs between the double extreme and the break of structure. Once a valid break and retest occur, the remaining sequence frequently completes.

## H4 health at confirmation

- 50 of 83 confirmations had aligned and expanding H4 averages;
- 19 had aligned and stable H4 averages;
- 69 of 83, or 83.13%, were aligned healthy in total;
- 14 were mixed or conflicted.

This supports the conceptual relationship between confirmed structure and diverging H4 averages at the start of a trend.

## Persistence

Each confirmation initiated one active structural run:

- bullish median duration: 24.5 D1 bars; mean 54.1; maximum 350;
- bearish median duration: 46 D1 bars; mean 96.3; maximum 557.

The D1 state is therefore a slow strategic regime state, not a frequent setup trigger.

## Monthly location and reach — descriptive only

Direction at the monthly open was sampled from the last completed D1 state before the month began.

| Side | Monthly zone | Target | Opportunities | Reached before invalidation | Rate |
|---|---|---|---:|---:|---:|
| Bull | M2–P | M4 | 42 | 5 | 11.90% |
| Bull | M2–P | R2 | 42 | 2 | 4.76% |
| Bear | P–M3 | M1 | 62 | 14 | 22.58% |
| Bear | P–M3 | S2 | 62 | 10 | 16.13% |

These rates do not yet measure incremental direction value. The study did not preregister a matched all-month or opposite-direction control, and no execution price was modeled.

## Independent audit finding

At the original trend-confirmation bar, H4 health was aligned in 83.13% of cases. At later monthly opens, however, only 2 of the 104 unique direction-plus-zone opportunities still had H4 moving averages aligned and stable/expanding with the old D1 direction.

This means the D1 state is too persistent to represent current technical trend health by itself. Applying the user's complete framework would abstain on nearly every monthly opportunity unless a faster current-trend layer is added.

## Interpretation

The D1 sequence should be retained unchanged as a **strategic trend-transition and regime state**. It should not be relaxed merely to manufacture more events.

The failed count gate does show that it is unsuitable as the sole current-direction unit for monthly opportunity attribution. The next valid research path is a frozen H4 structural sensitivity using the same dimensionless sequence and ATR-scaled tolerances:

- H4 double bottom/top;
- H4 break of structure;
- H4 retest;
- H4 higher low/lower high;
- H4 continuation confirmation;
- H4 EMA21/55/200 health at the same completed timestamp.

D1 remains the strategic context. H4 becomes the candidate current technical direction. No parameter search is authorized.

## Protected boundaries

- the 83 D1 events remain the frozen reference census;
- the failed 300-event gate is not redefined after seeing the outcome;
- no D1 tolerance is loosened;
- no pair, year or direction is discarded;
- monthly reach remains descriptive;
- macro, regime and seasonality attribution remains unopened;
- execution, Pine and deployment remain blocked.

## Artifact hashes

- `wayne_direction_census_decision.json`: `de58ad73c61f0035a611b894e0194fd55f1bc4df1dc0189ea1f7da5cb5db218d`;
- `wayne_direction_pair_census.csv`: `624334a7a345162692db1e71d75db3cd1cde63dbf36b11a43f32217163eb0e2b`;
- `wayne_direction_confirmation_health.csv`: `54116998195da20274575f9a32d00ac802123d4ebde3162fb6db3adaf6415b77`;
- `wayne_direction_monthly_reach_summary.csv`: `1a18f9e8de09c4f2bf7b3d5aa2d50af329ecf7f8cf23bf9fc59345c1017cb578`;
- `wayne_direction_pooled_structure_ledger.csv`: `019665f284f15f6f4c65e4efa35402b501512d935faf24ff6f51e09891318eb4`;
- `wayne_direction_pooled_monthly_reach.csv`: `2166896914a94c44a5138d52ec414cd1405f98ccf248492c7d173c3ab77feafd`.
