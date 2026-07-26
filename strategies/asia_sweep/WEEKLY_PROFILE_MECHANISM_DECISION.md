# Asian Sweep Weekly-Profile Mechanism — Decision

Date: 2026-07-26  
Decision: `FAIL_WEEKLY_PROFILE_MECHANISM_STOP`  
Development: EURUSD and GBPUSD, 2015–2019  
Protected: 2020–2025 unopened

## Authoritative evidence

- GitHub Actions run: `30214901504`;
- evaluated head: `13f92b08e59775f2cbd5aa7d688de9cf29b60619`;
- complete artifact: `asia-sweep-weekly-profile-pr-decision`;
- artifact digest: `sha256:56d5d81ac541805d896f3d80bb1ed160212a475e57a57d47ba4ecf4e4560d7ce`;
- frozen candidates completed: 10 of 10 H1/H2 target tests;
- focused tests, lint, development-source isolation, both pair ledgers and aggregate decision completed successfully.

The workflow is red only because the deliberate scientific authorization step requires `PASS_WEEKLY_PROFILE_MECHANISM_OPEN_MODELING`, while the authoritative result is the frozen negative decision above.

## Integrity and protected-data boundary

The qualified source artifact contains later years for reuse by other programmes. Before feature construction, the workflow copied exactly the ten 2015–2019 BID/ASK files for each pair into an isolated development directory. All regime construction and outcome evaluation ran against those directories only.

- no 2020–2025 file entered either development directory;
- daily trend features used completed days only;
- current-week context stopped strictly before the event entry timestamp;
- the entry/sweep bar and all later weekly information were excluded;
- immutable T0 target outcomes came from authoritative extended-reversal run `30209186651`.

## Pair census

| Pair | Source T0 events | Enriched T0 events | Warm-up/insufficient-context skips | Target rows | H1 resumption events | H2 retracement-continuation events |
|---|---:|---:|---:|---:|---:|---:|
| EURUSD | 1,220 | 1,199 | 21 | 5,993 | 102 | 16 |
| GBPUSD | 1,286 | 1,264 | 22 | 6,319 | 91 | 20 |
| **Pooled** | **2,506** | **2,463** | **43** | **12,312** | **193** | **36** |

## H1 — HTF trend resumption after early-week countertrend retracement

The frozen H1 population required:

- a non-neutral structural trend;
- Monday through Wednesday;
- a countertrend excursion of at least 0.35 ATR;
- proposed sweep reversal aligned with the structural trend;
- no mature with-trend extension of at least 0.75 ATR.

H1 did not merely miss the promotion thresholds. It underperformed its broader Monday–Wednesday HTF-aligned reference population for every target.

| Target | Events | Positives | Hit rate | Reference hit rate | Absolute lift | Relative lift | Mean stressed EV proxy | Median stressed R:R | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| Opposite boundary by 11:00 | 193 | 16 | 8.29% | 11.56% | -3.27 pp | 0.72x | -0.633R | 4.07R | Fail |
| 2R by 11:00 | 193 | 43 | 22.28% | 26.44% | -4.17 pp | 0.84x | -0.349R | 1.93R | Fail |
| Opposing liquidity by 14:00 | 193 | 22 | 11.40% | 14.54% | -3.14 pp | 0.78x | -0.439R | 4.16R | Fail |
| 3R by 12:00 | 193 | 32 | 16.58% | 19.96% | -3.38 pp | 0.83x | -0.355R | 2.90R | Fail |
| 4R by 14:00 | 193 | 25 | 12.95% | 16.64% | -3.68 pp | 0.78x | -0.371R | 3.88R | Fail |

No H1 target had positive EV in either pair or any of the five development years. The result directly rejects the simple proposition that a 0.35-ATR early-week countertrend move makes the next Asian Sweep reversal in the old HTF direction more executable.

## H2 — continuation of an active Monday/Tuesday retracement

The frozen H2 population required:

- a non-neutral structural trend;
- Monday or Tuesday;
- current-week displacement opposite the structural trend;
- a countertrend excursion of at least 0.20 ATR;
- proposed sweep trade aligned with that active retracement.

Only 36 events qualified, versus the frozen minimum of 120, and neither pair reached the minimum 40 events.

| Target | Events | Positives | Hit rate | Reference hit rate | Absolute lift | Mean stressed EV proxy | Result |
|---|---:|---:|---:|---:|---:|---:|---|
| 2R by 11:00 | 36 | 9 | 25.00% | 24.50% | +0.50 pp | -0.267R | Fail |
| Opposite boundary by 11:00 | 36 | 4 | 11.11% | 10.26% | +0.85 pp | -0.511R | Fail |
| 3R by 12:00 | 36 | 6 | 16.67% | 17.95% | -1.28 pp | -0.351R | Fail |
| Opposing liquidity by 14:00 | 36 | 5 | 13.89% | 12.54% | +1.35 pp | -0.343R | Fail |
| 4R by 14:00 | 36 | 5 | 13.89% | 13.96% | -0.07 pp | -0.323R | Fail |

H2 is both underpowered and economically negative. It does not authorize a retracement-continuation model.

## Binding decision

`FAIL_WEEKLY_PROFILE_MECHANISM_STOP`

Consequences:

- no H1 or H2 target is selected;
- regime-aware modelling for these two hypotheses is not opened;
- no reversal/continuation/abstention router is fitted from H1/H2;
- no position-structure P&L is opened;
- no Pine, alerts, paper trading or deployment is authorized;
- 2020–2025 remains unopened by this work package;
- no threshold, pair, year, weekday, direction, target or subgroup rescue is permitted.

## Descriptive discovery outside the H1/H2 promotion contract

A complete audit of the other already-frozen weekly phases exposed one materially different pattern:

- phase: `MIDWEEK_REVERSAL_OR_TRANSITION`;
- current week had displaced at least 0.75 ATR against the old structural trend from Wednesday onward;
- proposed sweep trade continued that developing transition, rather than reverting to the old structural trend;
- discovery population: 85 events, 45 EURUSD and 40 GBPUSD.

Descriptive 2015–2019 evidence:

| Target | Events | Hit rate | Mean stressed EV proxy | EURUSD EV | GBPUSD EV | Positive years |
|---|---:|---:|---:|---:|---:|---:|
| Opposing liquidity by 14:00 | 85 | 27.06% | +0.309R | +0.317R | +0.300R | 4 of 5 |
| Fixed 4R by 14:00 | 85 | 27.06% | +0.311R | +0.289R | +0.336R | 3 of 5 |
| Fixed 3R by 12:00 | 85 | 28.24% | +0.094R | +0.031R | +0.164R | 4 of 5 |
| Opposite boundary by 11:00 | 85 | 23.53% | +0.077R | +0.107R | +0.044R | 4 of 5 |
| Fixed 2R by 11:00 | 85 | 35.29% | +0.026R | +0.096R | -0.052R | 2 of 5 |

This result has **no promotion authority** because it was identified in the post-decision descriptive audit. It may only motivate a new, separately frozen out-of-sample hypothesis. It may not be used to change H1/H2 or reclassify their failure.

## Strategic interpretation

The typical weekly-profile observation was valid, but the first implementation produced an important distinction:

- an early countertrend retracement did not make the next reversal back toward the old HTF trend better;
- a small Monday/Tuesday retracement-continuation population was too rare and negative;
- the potentially useful state appears later, when the countertrend weekly move has become large enough to represent a **developing structural transition**, and the actionable sweep continues that transition rather than fading it.

The next legitimate path is therefore not another trend-resumption filter. It is a new out-of-sample **weekly-transition continuation** hypothesis, frozen before any 2020–2025 access.