# Wayne Independent FX Replication — Independent Audit v1.0

Date: 2026-07-27  
Audit verdict: `PASS_PROCESS_AND_RECOMPUTATION`  
Research verdict audited: `FAIL_INDEPENDENT_REPLICATION_SAMPLE`

## Audit scope

The audit independently checked:

- source-panel freeze timing;
- admitted instruments and years;
- absence of development instruments and locked years;
- ledger uniqueness and target structure;
- treatment and target-availability counts;
- treatment and control reach rates;
- cluster bootstrap intervals;
- instrument-year-stratified, instrument-month bundle-preserving permutation p-values;
- pair concentration;
- pair and year breadth;
- leave-one-pair-out effects;
- binding application of the preregistered decision table.

## Governance audit

Passed:

- the candidate universe and source gates were frozen before outcomes;
- `INDEPENDENT_FX_PANEL_MANIFEST_V0_9.md` was committed before the sequence workflow released pair construction;
- all 28 annual source-quality records were regenerated in CI and matched the committed ledger;
- only EURGBP, EURJPY, GBPJPY and NZDUSD entered the outcome ledger;
- only 2015-2021 entered the ledger;
- no development pair entered the independent estimate;
- no threshold, target, landmark, structure, MA-health or availability rule changed;
- no yield, VIX, macro, seasonality or execution data entered the study.

## Ledger audit

Observed:

- pooled target rows: 2,106;
- unique instrument-opportunity records: 1,053;
- exactly two target tiers per opportunity;
- no duplicate `instrument + opportunity_id + target_tier` key;
- exact instrument set: EURGBP, EURJPY, GBPJPY and NZDUSD;
- exact year set: 2015-2021.

No key collision, duplicate target record, development-pair contamination or locked-year contamination was found.

## Exact statistical recomputation

The audit implementation read only the frozen pooled ledger and independently reconstructed the primary and secondary comparison populations.

### Day-10 conservative

Recomputed exactly:

- treatment N: 14;
- control N: 447;
- treatment reach: 35.7142857143%;
- control reach: 12.5279642058%;
- lift: 23.1863215085 percentage points;
- 90% instrument-month cluster bootstrap: +1.6196684925 to +45.1347433498 percentage points;
- bundle-preserving clustered permutation p: 0.0989802039592.

### Day-10 stretch

Recomputed exactly:

- treatment N: 20;
- control N: 469;
- treatment reach: 40.0000000000%;
- control reach: 7.8891257996%;
- lift: 32.1108742004 percentage points;
- 90% instrument-month cluster bootstrap: +14.2630824373 to +50.2222405161 percentage points;
- bundle-preserving clustered permutation p: 0.0003999200160.

Every recomputed count, rate, effect, confidence bound and p-value matched the workflow decision JSON to floating-point precision.

## Inference audit

The permutation routine preserved:

- the instrument-month cluster as the causal bundle;
- bull/bear treatment vectors within each cluster;
- same-size cluster exchange only;
- instrument-year strata;
- the frozen one-sided positive-lift test;
- 5,000 permutations and the frozen seeds.

The bootstrap routine sampled complete instrument-month clusters with replacement and used 2,000 frozen-seed draws.

No row-level treatment shuffling was used.

## Sample-gate audit

The binding sample decision was correctly applied:

- 26 active sequences < 80;
- 14 available conservative treatments < 40;
- 447 controls >= 120;
- 2 pairs with at least 8 active sequences < 4;
- 1 pair with at least 5 available treatments < 4.

Because at least one gate failed, the preregistration required `FAIL_INDEPENDENT_REPLICATION_SAMPLE`. Four of five gates failed. The workflow correctly prevented the descriptive effect estimates from opening the yield phase.

## Effect-criterion audit

Even if the sample gate were ignored, the primary conservative endpoint would not satisfy the complete frozen replication criteria:

- clustered p was 0.0990, above 0.05;
- only one pair had enough observations for formal pair breadth;
- only two years qualified as positive under the existing cell-size rule;
- treatment concentration was 57.14%, above 35%.

The positive bootstrap lower bound and positive leave-one-pair-out effects do not supersede these failures.

## Secondary-endpoint audit

The day-10 stretch result was favorable, but the audit confirms that it cannot replace the conservative primary endpoint after the fact.

Promoting it would violate:

- endpoint hierarchy;
- frozen sample gates;
- pair-breadth requirements;
- the no-rescue rule.

It is retained as descriptive evidence only.

## Audit conclusion

The workflow implementation, source freeze, pooled ledger, cluster-preserving inference and binding decision are internally consistent and reproducible.

The correct research conclusion is:

`FAIL_INDEPENDENT_REPLICATION_SAMPLE`

The result does not authorize yields, VIX, macro, seasonality, execution or Pine development. Closing the active Wayne direction-first line is consistent with both the frozen research contract and efficient research allocation.

## Evidence identity

Authoritative workflow: `30265303447`  
Head: `5b4a3121b58f1a485a61e433b5840c3f8b419c72`  
Artifact ID: `8652653494`  
Artifact digest: `sha256:2428fc95da32599b933030b5e52db01829bcfbb5c566b8eddcf1c8233acece9a`
