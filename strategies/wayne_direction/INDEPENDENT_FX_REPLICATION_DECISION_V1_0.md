# Wayne Independent FX Replication Decision v1.0

Date: 2026-07-27  
Source-panel qualification run: `30259833965`  
Authoritative replication run: `30260573288`  
Decision artifact: `wayne-independent-fx-replication-decision`  
Artifact digest: `sha256:cbed0761c03e9b71793b0100b23e04884db0d99154539a0e814930dc012251b9`

## Binding decision

`FAIL_REPLICATION_SAMPLE_INSUFFICIENT`

The independent panel reproduced the positive direction and a material conservative-target lift. It did not satisfy the preregistered clean-treatment sample or breadth requirements and therefore does not authorize yield, VIX, execution or deployment research.

## Frozen independent panel

- EURGBP
- EURJPY
- GBPJPY
- NZDUSD

Period: 2015–2021 only.  
Protected 2022–2025 partitions were not opened.

The monthly location, H4 structural sequence, H4 EMA21/55/200 health definition, day-10 landmark, target definitions, target-availability rules and cluster inference were unchanged from the original six-pair development study.

## Opportunity census

- primary close-in-zone opportunities: 514;
- active day-10 sequences: 26;
- active day-10 pair breadth: three pairs with at least three events;
- largest pair contribution: EURJPY, 11 of 26 = 42.31%.

| Pair | Primary opportunities | Active day-10 |
|---|---:|---:|
| EURGBP | 130 | 5 |
| EURJPY | 133 | 11 |
| GBPJPY | 121 | 8 |
| NZDUSD | 130 | 2 |
| **Total** | **514** | **26** |

## Conservative target — primary replication endpoint

Among conservative targets still available after the fixed day-10 landmark:

- treatment: 14;
- controls: 447;
- treatment reach: 5 of 14 = 35.71%;
- control reach: 56 of 447 = 12.53%;
- reach lift: +23.19 percentage points;
- authoritative cluster-permutation p-value: 0.0948;
- cluster bootstrap 90% interval: +1.48 to +43.70 percentage points.

The effect clears the frozen +10 percentage-point and p≤0.10 gates and agrees directionally with the original six-pair result. It does not clear the minimum of 15 clean treatment observations.

### Why 26 active sequences produced only 14 clean treatments

Twelve conservative targets were not eligible at the landmark because the nearer M4/M1 target had already been touched before confirmation or was same-bar ambiguous.

| Pair | Active | Clean available | Unavailable/pre-consumed | Subsequent reaches |
|---|---:|---:|---:|---:|
| EURGBP | 5 | 2 | 3 | 1 |
| EURJPY | 11 | 8 | 3 | 3 |
| GBPJPY | 8 | 2 | 6 | 0 |
| NZDUSD | 2 | 2 | 0 | 1 |
| **Total** | **26** | **14** | **12** | **5** |

This is a causal eligibility consequence, not missing data. The unavailable targets cannot be restored without changing the frozen methodology.

## Conservative breadth

Only EURJPY had at least three treatment and three control observations at pair level:

- EURJPY: 3 of 8 treatment reaches versus 19 of 113 controls; +20.69 percentage points;
- EURGBP: 2 treatments, ineligible for pair-effect gate;
- GBPJPY: 2 treatments, ineligible;
- NZDUSD: 2 treatments, ineligible.

Year-level treatment availability was also sparse:

- 2015: four treatments, effect −9.43 percentage points;
- 2018: three treatments, effect +19.49 percentage points;
- 2021: three treatments, effect +49.02 percentage points;
- 2016 and 2017: no clean treatments;
- 2019 and 2020: two treatments each and ineligible.

Therefore:

- positive eligible pairs: 1, required 3;
- positive eligible years: 2, required 4;
- maximum pair concentration: 42.31%, required no more than 40%.

## Stretch target — supportive only

The farther R2/S2 target remained available more often:

- treatment: 20;
- controls: 469;
- treatment reach: 40.00%;
- control reach: 7.89%;
- lift: +32.11 percentage points;
- cluster-permutation p-value: 0.0002;
- bootstrap 90% interval: +13.94 to +50.51 percentage points;
- positive eligible pairs: 3;
- positive eligible years: 3.

This is notable supporting evidence, but the preregistration explicitly prevents the stretch endpoint from rescuing a failed conservative primary endpoint.

## Frozen gate result

### Sample

- PASS — at least 20 active day-10 opportunities: 26;
- **FAIL** — at least 15 clean conservative treatments: 14;
- PASS — at least 200 controls: 447;
- PASS — at least three active opportunities in three pairs.

### Effect

- PASS — conservative lift at least 10 percentage points;
- PASS — clustered p-value at most 0.10;
- PASS — positive direction agrees with original panel.

### Breadth and concentration

- **FAIL** — no pair above 40%: EURJPY 42.31%;
- **FAIL** — positive effect in three eligible pairs: one;
- **FAIL** — positive effect in four eligible years: two.

## Interpretation

The independent result is not a negative effect replication. Both the conservative and stretch estimates are directionally supportive, and the conservative interval excludes zero at the preregistered 90% level.

The result nevertheless remains non-promotable because the setup is operationally sparse once causal target availability is enforced. The independent panel does not establish cross-pair or cross-year breadth.

## Consequence

The following remain closed:

- nominal two-year yield attribution;
- VIX risk-regime attribution;
- seasonality and release-level macro;
- entry, stop, partial-exit, runner or cost research;
- P&L, sizing, Pine, alerts, paper trading or deployment;
- 2022–2025 chronological confirmation.

A further technical study requires a new strategic decision. The only defensible continuation would be one final preregistered independent source panel with no changes to the signal or targets. It must not reuse 2022–2025 as sample rescue and must not tune the day-10 sequence.
