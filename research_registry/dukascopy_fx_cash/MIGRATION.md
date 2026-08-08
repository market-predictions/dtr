# Historical Dukascopy FX Cash Migration

The registry is mandatory prospectively. Historical backfill is evidence reconstruction, not a mass rename exercise.

`migration_candidates.json` lists branches whose names indicate possible use of the ten-pair Dukascopy FX cash source. Each candidate must be opened and verified before a DFXC study ID is assigned.

For each historical candidate:

1. verify it actually used the canonical cash-FX dataset rather than a Dukascopy static proxy or another source;
2. identify the smallest scientific decision unit(s);
3. freeze the exact producing commit, not current mutable branch state;
4. preserve the original decision verbatim;
5. record data windows and any prior holdout exposure;
6. classify assurance from evidence, never from assumption;
7. register superseded intermediate studies when they contain reusable methodology/results;
8. link broader later studies through `related_studies`.

Priority backfill: final baselines/falsification studies, studies with holdout consequences, rejected hypotheses likely to be rediscovered, ablations, then exploratory diagnostics.
