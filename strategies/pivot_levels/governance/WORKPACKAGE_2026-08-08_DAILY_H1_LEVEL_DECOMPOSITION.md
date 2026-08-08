# Work Package — PIV-WP-20260808-06

Date: 2026-08-08
Study: `DFXC-20260808-006-pivot-daily-level-decomposition`
Role: `implementation_operations`
Status: `IMPLEMENTATION_COMPLETE_ASSURANCE_PENDING`

## Objective

Decompose the confirmed Daily classic-pivot × H1 wick association by named level, with a frozen primary comparison of S1/R1 versus S2/R2 and no post-hoc level selection.

## Required controls

- permanent Dukascopy FX Cash cache only;
- frozen Daily/H1 parent pivot/zone/wick definitions;
- exact reconstruction of the holdout observation population before accepting named-level diagnostics;
- explicit separation of exact geometry reproduction from non-exact retired terminal-ledger reconstruction;
- pair/year breadth and detector-reconstruction sensitivity;
- no conversion of the diagnostic into a trading rule.

## Candidate decision

`DIAGNOSTIC_FIRST_ORDER_PIVOTS_DOMINATE_SECOND_ORDER_PIVOTS_REQUIRES_EXACT_LEDGER_OR_FRESH_CONFIRMATION`

## Governance state

Implementation is complete. Independent `governance_release_assurance` is required before this work package is considered scientifically closed.
