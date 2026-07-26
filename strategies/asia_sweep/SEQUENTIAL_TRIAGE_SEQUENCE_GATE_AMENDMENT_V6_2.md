# Sequential Triage Role and Sequence Gate — Amendment v6.2

Date: 2026-07-26
State: FROZEN_BEFORE_FORMAL_PHASE_A_DECISION
Branch: `agent/asia-sweep-sequential-triage`

## Reason

The v6.0 programme estimates all three states at T0–T3, but a staged architecture does not require every landmark to make both directional decisions. T0 may correctly remain mostly abstinent; continuation protection is expected earlier than reversal confirmation.

This amendment defines the deterministic sequence-level Phase A gate before staged-policy P&L is opened.

## Roles

### Provisional landmark

T0 is descriptive and may support a later Phase B policy with 0R, 0.25R or 0.50R provisional risk. T0 is not required to pass both directional precision gates. It must remain causal and calibrated, and is reported in full.

### Continuation-protection landmark

Select the earliest landmark in `T1, T2, T3` that satisfies, on pooled leave-one-year-out decisions:
- continuation precision >= 0.45;
- continuation decisions in both pairs and at least four of five years;
- continuation decision coverage >= 5%;
- calibrated continuation Brier score below the class-frequency comparator;
- no pair, weekday or decision concentration above 70%.

This landmark may authorize `EXIT`, `REDUCE`, and `BLOCK_ADD`. It does not yet authorize a continuation trade; continuation execution remains a separate Phase C/D research output.

### Reversal-confirmation landmark

Select the earliest landmark in `T1, T2, T3` that satisfies:
- reversal precision >= 0.40;
- reversal decisions in both pairs and at least four of five years;
- reversal decision coverage >= 5%;
- calibrated reversal Brier score below the class-frequency comparator;
- no pair, weekday or decision concentration above 70%.

This landmark may authorize `HOLD` or `ADD` in Phase B, subject to total risk <=1R.

## Common sequence gates

A model family passes Phase A only when:
- both a continuation-protection and reversal-confirmation landmark exist;
- mean macro one-vs-rest PR-AUC relative lift across the two selected landmarks >= 0.35;
- each selected landmark has at least 400 rows and 150 per pair;
- each selected landmark's abstention coverage is between 25% and 75%;
- all three calibrated class Brier scores beat class-frequency comparators at both selected landmarks;
- selected decisions are present in both pairs and at least four of five years;
- maximum actionable concentration is <=70%.

The same model family must supply both selected landmarks. Per-landmark family switching is prohibited.

## Selection hierarchy

1. Evaluate the elastic-net sequence.
2. Evaluate the HGB sequence.
3. Use elastic net when it passes.
4. HGB may replace a passing elastic-net sequence only under the v6.1 improvement rule.
5. If only HGB passes, HGB is selected.
6. If neither passes, Phase B remains closed.

## Conflict transitions

For Phase A reporting, every landmark emits `REVERSAL`, `CONTINUATION`, or `ABSTAIN` under v6.1.

For later staged simulation:
- a continuation decision always closes/reduces reversal exposure and blocks adds;
- a later reversal decision may not reopen on the same bar after a continuation exit;
- a new direction can be considered only at the next active minute;
- ambiguous simultaneous directional qualification remains `ABSTAIN`.

## Protected boundary

This amendment does not open P&L and does not authorize continuation trading. It only defines whether the classification sequence is strong enough to proceed to separately gated staged-reversal and continuation-geometry studies.
