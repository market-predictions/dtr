# Independent FX Source Qualification Amendment v0.8.1

Date: 2026-07-27  
Status: `FROZEN_BEFORE_WAYNE_OUTCOMES`  
Parent: `INDEPENDENT_FX_REPLICATION_PREREGISTRATION_V0_8.md`

## Purpose

Operationalize the source-quality gates in v0.8 before any independent Wayne staged-sequence outcome is generated or viewed.

This amendment changes no candidate, technical, target, sample, effect or decision rule. It only fixes deterministic source-diagnostic procedures where the parent preregistration stated a principle rather than an executable formula.

## Calendar and synchronization

- Every annual BID and ASK file must equal the complete UTC calendar-minute grid for its year.
- The FX expected-open calendar is defined in `America/New_York` local time:
  - Sunday from 17:00 inclusive;
  - Monday through Thursday continuously;
  - Friday until 17:00 exclusive.
- IANA timezone conversion is used, so daylight-saving transitions are handled by the timezone database rather than fixed UTC offsets.
- A minute is active only when both BID and ASK have `is_active_quote = 1` and both quote records pass OHLC validity.
- BID/ASK timestamp alignment is the intersection divided by the union of retained timestamps.

## Duplicate and annual-overlap treatment

- Raw duplicate share is the number of rows participating in a duplicate timestamp divided by total rows.
- Deterministic duplicate handling retains the final occurrence, although a full-grid file with any duplicate necessarily fails exact-grid integrity.
- An annual overlap exists when the first timestamp of a year is not strictly later than the prior partition's final timestamp.

## Quote validity

For BID and ASK separately:

- all OHLC values must be finite and positive;
- `high >= max(open, close)`;
- `low <= min(open, close)`.

Close spread is `ASK close - BID close`. Spread and relative-spread diagnostics use synchronized active valid minutes. Relative spread divides close spread by the BID/ASK midpoint close.

## Temporal coverage and gap counting

- Annual coverage is synchronized active valid expected-open minutes divided by all expected-open minutes.
- Inactive runs are measured on the compressed expected-open-minute ordinal, so the routine Friday-to-Sunday closure contributes no gap minutes.
- A gap longer than one trading day is strictly greater than 1,440 expected-open minutes.
- A gap longer than five trading days is strictly greater than 7,200 expected-open minutes.

## Trading-day activity

- The named FX trading day starts at 17:00 New York time.
- Adding seven hours to New York local timestamps maps each 17:00 start to midnight of the following named trading date.
- Distinct trading days are named dates with at least one synchronized active valid quote.
- Median and 10th-percentile active minutes are calculated across those active trading dates.

## Persistent activity collapse

The qualitative Q6 collapse clause is fixed as follows:

- calculate expected-open coverage for each complete named calendar month;
- calculate the pair's seven-year median monthly coverage;
- define a collapsed month as coverage below 80% of that seven-year median;
- Q6 fails when two consecutive complete months are collapsed.

This is intentionally a severe source-outage detector, not a market-liquidity optimizer.

## Frozen source run

Qualification uses only artifacts from source workflow run `30111481052`, head `6bebbfe07318535cb54569e8dcca1f5a84753ca2`.

Pairs absent from that frozen qualified-source run fail Q1 as unavailable. They are not downloaded after observing independent Wayne outcomes.

## Governance

- source diagnostics may be viewed because they contain no Wayne treatment or reach outcome;
- the admitted panel must be committed before sequence generation;
- the panel cannot subsequently be modified because of a favorable or unfavorable replication result;
- 2022–2025, yields, VIX, macro, seasonality, execution and Pine remain locked.
