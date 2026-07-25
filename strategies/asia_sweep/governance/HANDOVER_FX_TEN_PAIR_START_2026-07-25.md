# Handover — Asian Sweep Ten-Pair FX Discovery Start

Date: 2026-07-25  
Work package: `AS-WP-20260725-10`

## Delivered before real-data execution

- dedicated branch and separate Asian Sweep namespace;
- ten-pair qualified-source cache reuse;
- fixed 2015–2019 discovery partition;
- unchanged auction-state rejection semantics;
- pair-level matched-control study engine;
- pooled date-clustered gate engine;
- synthetic matching and all-pass gate tests;
- protected GitHub Actions matrix;
- preregistration, status, roadmap and changelog.

## Scientific boundary

The first workflow may inspect only 2015–2019 mechanism outcomes. It may not calculate executable P&L or open 2020 onward data. Failure closes the current formulation before strategy construction.

## Operational boundary

Each pair writes and uploads compact evidence independently. The aggregate job runs after all pair jobs and preserves the pooled decision before enforcing pass/fail.

## Next autonomous action

Open the draft pull request, observe focused tests and pair jobs, inspect preserved evidence, independently reconstruct the decision, and continue to 2020–2021 only after every frozen discovery predicate passes.
