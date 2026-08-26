# Wayne Independent FX Replication Decision v1.0

Date: 2026-07-27  
Status: `COMPLETE_BINDING_SAMPLE_FAIL`  
Binding decision: `FAIL_INDEPENDENT_REPLICATION_SAMPLE`

## Executive conclusion

The exact frozen day-10 monthly-location -> new H4 structure -> healthy aligned EMA sequence was replicated without threshold changes on the independently qualified panel:

- EURGBP;
- EURJPY;
- GBPJPY;
- NZDUSD.

The source panel passed every frozen Q1-Q6 data gate for 2015-2021, and its manifest was committed before any Wayne outcome was generated.

The technical sequence remained rare. The independent panel produced only 26 active day-10 opportunities and 14 target-available conservative treatment rows. The frozen gates required 80 and 40 respectively. Pair breadth also failed materially.

Therefore the result is a binding sample failure regardless of the descriptive reach differences. The yield, VIX, macro, seasonality, execution and Pine phases remain closed.

## Frozen sample decision

| Gate | Observed | Required | Result |
|---|---:|---:|---|
| Active day-10 sequences | 26 | 80 | FAIL |
| Available conservative treatments | 14 | 40 | FAIL |
| Available controls | 447 | 120 | PASS |
| Pairs with at least 8 active sequences | 2 | 4 | FAIL |
| Pairs with at least 5 available treatments | 1 | 4 | FAIL |

### Pair census

| Pair | Active day-10 sequences | Available conservative treatments |
|---|---:|---:|
| EURGBP | 5 | 2 |
| EURJPY | 11 | 8 |
| GBPJPY | 8 | 2 |
| NZDUSD | 2 | 2 |

EURJPY supplied 8 of the 14 available conservative treatments, giving a treatment concentration of 57.14%. The frozen maximum was 35%, conditional on sample-gate passage.

## Frozen comparisons

These results are descriptive because the sample gate failed.

| Endpoint | Treatment N | Control N | Treatment reach | Control reach | Lift | Clustered p | FDR q | 90% cluster bootstrap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Day-10 conservative | 14 | 447 | 35.71% | 12.53% | +23.19 pp | 0.0990 | 0.0990 | +1.62 to +45.13 pp |
| Day-10 stretch | 20 | 469 | 40.00% | 7.89% | +32.11 pp | 0.0004 | 0.0008 | +14.26 to +50.22 pp |

The conservative endpoint was the primary replication endpoint. It did not meet the clustered significance criterion and contained only 14 treatments.

The stretch result was statistically strong descriptively, but it cannot promote the model because:

1. it was the secondary endpoint;
2. the overall and pair-level sample gates failed;
3. only 20 treatment rows were available;
4. the research contract forbids substituting a favorable secondary endpoint after a primary sample failure.

## Conservative pair results

| Pair | Treatment reach | Control reach | Descriptive lift |
|---|---:|---:|---:|
| EURGBP | 1/2 = 50.00% | 16/115 = 13.91% | +36.09 pp |
| EURJPY | 3/8 = 37.50% | 19/113 = 16.81% | +20.69 pp |
| GBPJPY | 0/2 = 0.00% | 8/102 = 7.84% | -7.84 pp |
| NZDUSD | 1/2 = 50.00% | 13/117 = 11.11% | +38.89 pp |

Only EURJPY had enough treatment rows to qualify for the existing pair-effect breadth calculation. The other apparent pair differences are based on two treatments each and cannot be treated as pair evidence.

## Year breadth

- 2015 was negative;
- 2016 and 2017 had no available conservative treatments;
- 2018, 2019, 2020 and 2021 were descriptively positive;
- only two years met the existing minimum cell sizes required for formal positive-year breadth.

This does not satisfy the frozen requirement of at least four positive eligible years.

## Leave-one-pair-out diagnostic

The conservative pooled lift remained positive after removing any single pair:

| Removed pair | Remaining treatments | Remaining controls | Lift |
|---|---:|---:|---:|
| EURGBP | 12 | 332 | +21.29 pp |
| EURJPY | 6 | 334 | +22.26 pp |
| GBPJPY | 12 | 345 | +27.75 pp |
| NZDUSD | 12 | 330 | +20.30 pp |

This is encouraging as a descriptive robustness check, but it cannot overcome the sample and concentration failures.

## Development versus independent interpretation

The six-pair development panel produced:

- 36 active day-10 sequences;
- 25 available conservative treatments;
- conservative lift of +35.69 pp.

The independent panel produced:

- 26 active day-10 sequences;
- 14 available conservative treatments;
- conservative lift of +23.19 pp.

The sign remained positive, but the independent effect was smaller and statistically unresolved. Development and replication must not be pooled to declare success. Pooling would consume the independence of the replication and still would not repair the pair-breadth problem.

## Strategic decision

### What is retained

- monthly pivot location remains a coherent market-location concept;
- the ordered location -> H4 structure -> H4 MA-health architecture remains logically sound;
- completed sequences may identify unusually directional months;
- the result remains a research observation suitable for future independent study.

### What is rejected for the active roadmap

- the sequence is not a sufficiently frequent standalone FX decision edge on the tested 2015-2021 universe;
- it cannot support a conditional strategy programme at present;
- it does not justify engineering yield, VIX, macro or seasonality filters around this setup;
- it does not justify execution, entry, stop, target, sizing, alert or Pine development.

## Next-step ruling

The active Wayne direction-first line stops here.

Not authorized:

- opening 2022-2025 to rescue sample;
- loosening structure or EMA-health definitions;
- replacing the conservative endpoint with the favorable stretch endpoint;
- downloading selectively chosen additional FX pairs after viewing these outcomes;
- adding yield, VIX, macro or seasonality conditions;
- converting descriptive reach into P&L.

A future study would require a genuinely new preregistered cohort, materially more history or a separately justified asset family. That would be a new research programme rather than continuation or rescue of this result.

Given the user's preference for a simple phased approach, the recommended allocation decision is to close this line and redirect research effort to a strategy with materially higher event frequency and a clearer executable decision path.

## Authoritative evidence

Workflow run: `30265303447`  
Workflow head: `5b4a3121b58f1a485a61e433b5840c3f8b419c72`  
Decision artifact ID: `8652653494`  
Artifact digest: `sha256:2428fc95da32599b933030b5e52db01829bcfbb5c566b8eddcf1c8233acece9a`

Output hashes:

- `WAYNE_INDEPENDENT_REPLICATION_DECISION.md`: `6b25ecc99f1fb521a775d25fc9eb4beecf9a1443899beff3566a55137301e6a6`;
- `wayne_independent_comparisons.csv`: `9ea416bde338932203d9864f0fe359cbe0ae3fd59f9ca8903a6f316efd1f7266`;
- `wayne_independent_decision.json`: `da8d3c77c675155f4dfa9cd8145ff990d58fce3cb66b2ad34225d8b7b7f57998`;
- `wayne_independent_leave_one_pair_out.csv`: `56b5eca5c66c33f3b2e1a5a3d495d2423ca3a5b51280f0cc9885503c2a55a275`;
- `wayne_independent_pooled_ledger.csv`: `50c27e5ae7b2eefb2c3245889b66b2e6d8e8ee7579fee2025d96a5ec031a82af`;
- `wayne_independent_stage_census.csv`: `f163d72db83f8662c323ae023a54d29842afbb8cf58f5aef36a8ecc36f5b47c4`.
