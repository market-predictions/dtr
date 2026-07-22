# NQ Maintenance-Boundary Timestamp Census — 2026-07-22

## Decision

`SUPPORT_BAR_CLOSE_RETAIN_SHIFT_MINUS_ONE`

The registered NQ archive overwhelmingly supports timestamps that label the completed minute rather than the opening instant of the minute. The shift-minus-one timing-corrected engine remains the scientific working interpretation.

## Census contract

- Source archive SHA-256: `8d3f157a422636e5b8dda51cc3a3d9209c50cb53f9b279d3e14b627ce59370dc`.
- Candidate boundary: gap longer than 30 minutes whose first post-gap timestamp is between 18:00 and 18:10 Eastern Time.
- Normal boundary: prior timestamp at 16:59 or 17:00; earlier prior timestamps are retained as early-close/holiday evidence but excluded from the normal-mode decision.

## Result

- Candidate reopen gaps: **765**.
- Normal prior-close gaps: **735**.
- Normal `17:00 → 18:01`: **732**.
- Normal `16:59 → 18:00`: **0**.
- Any candidate reopening at exactly `18:00`: **0**.
- Isolated normal exceptions: one `16:59 → 18:01`, one `17:00 → 18:03`, and one `17:00 → 18:04`.
- Early-close/holiday patterns: 21 `13:00 → 18:01`, seven `13:15 → 18:01`, and two other shortened-session variants.

## Interpretation

A normal last label of 17:00 followed by a normal first label of 18:01 is the expected pattern when one-minute bars are stamped at bar close. A bar-open feed would ordinarily show the normal pair `16:59 → 18:00`, which is absent from the archive.

This census resolves the repository's working timestamp interpretation strongly enough to retain the pessimistic timing-corrected branch. It does not replace missing authoritative vendor metadata, but it removes the need to unwind the E6 research stack on the specific bar-open hypothesis.

## Consequence

- Preserve `DTR_CAUSAL_BAR_CLOSE_RANGE_SHIFT_MINUS1` as the scientific reference control.
- Do not restore the 495-trade bar-open result as the working engine.
- Keep source timestamp metadata as a documentation/provenance limitation rather than an unresolved binary engine choice.
