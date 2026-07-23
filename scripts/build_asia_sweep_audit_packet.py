from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

_FORBIDDEN_RESULT_TOKENS = (
    "pnl",
    "return",
    "realized",
    "exit_price",
    "exit_reason",
    "mfe",
    "mae",
)
_EDGE_REASONS = (
    "entry_at_or_after_window_end",
    "missing_minute_grid",
    "no_positive_volume_activity",
    "stale_quote_run_exceeded",
    "ambiguous_double_sweep",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_key(row: pd.Series) -> str:
    identity = "|".join(
        str(row.get(column, ""))
        for column in (
            "instrument",
            "trade_date",
            "execution_window",
            "variant",
            "status",
            "rejection_reason",
            "direction",
            "first_sweep_timestamp",
            "entry_timestamp",
        )
    )
    return hashlib.sha256(identity.encode()).hexdigest()


def _load_ledgers(report_root: Path) -> tuple[pd.DataFrame, list[dict[str, object]]]:
    paths = sorted(report_root.glob("*_event_ledger.csv"))
    if len(paths) != 4:
        raise ValueError(f"Expected four variant ledgers in {report_root}, found {paths}")

    frames: list[pd.DataFrame] = []
    inventory: list[dict[str, object]] = []
    for path in paths:
        frame = pd.read_csv(path)
        forbidden = [
            column
            for column in frame.columns
            if any(token in column.lower() for token in _FORBIDDEN_RESULT_TOKENS)
        ]
        if forbidden:
            raise ValueError(f"P&L or execution-result columns are prohibited: {forbidden}")
        frames.append(frame)
        inventory.append(
            {
                "file": path.name,
                "rows": int(len(frame)),
                "sha256": _sha256(path),
            }
        )
    combined = pd.concat(frames, ignore_index=True)
    return combined, inventory


def _deterministic_sample(frame: pd.DataFrame, count: int) -> pd.DataFrame:
    if len(frame) < count:
        raise ValueError(f"Need at least {count} events, found {len(frame)}")

    work = frame.copy()
    work["direction_label"] = work["direction"].map({1: "LONG", -1: "SHORT"}).fillna("NONE")
    work["stable_sample_key"] = work.apply(_stable_key, axis=1)
    work = work.sort_values(
        ["stable_sample_key", "trade_date", "execution_window", "variant"]
    )

    selected_parts: list[pd.DataFrame] = []
    edge = work[work["rejection_reason"].isin(_EDGE_REASONS)]
    if not edge.empty:
        selected_parts.append(
            edge.groupby("rejection_reason", dropna=False, group_keys=False).head(2)
        )

    strata = ["variant", "status", "execution_window", "direction_label"]
    selected_parts.append(work.groupby(strata, dropna=False, group_keys=False).head(1))
    selected = pd.concat(selected_parts, ignore_index=False).drop_duplicates(
        subset="stable_sample_key"
    )

    if len(selected) < count:
        remaining = work[~work["stable_sample_key"].isin(selected["stable_sample_key"])]
        selected = pd.concat(
            [selected, remaining.head(count - len(selected))],
            ignore_index=False,
        )

    selected = selected.head(count).sort_values(
        ["trade_date", "execution_window", "variant", "stable_sample_key"]
    )
    return selected.reset_index(drop=True)


def _counts(frame: pd.DataFrame, columns: list[str]) -> list[dict[str, object]]:
    return (
        frame.groupby(columns, dropna=False)
        .size()
        .rename("count")
        .reset_index()
        .to_dict(orient="records")
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--instrument", required=True)
    parser.add_argument("--sample-size", type=int, default=50)
    args = parser.parse_args()

    combined, inventory = _load_ledgers(args.report_root)
    if set(combined["instrument"].dropna().astype(str)) != {args.instrument}:
        raise ValueError("Ledger instrument does not match --instrument")

    sample = _deterministic_sample(combined, args.sample_size)
    sample_path = args.report_root / "manual_audit_sample_50.csv"
    sample.to_csv(sample_path, index=False)

    summary = {
        "instrument": args.instrument,
        "strategy_id": "ASIA_SWEEP_STANDALONE_V0",
        "purpose": "event semantics and manual audit only",
        "pnl_calculated": False,
        "execution_simulated": False,
        "combined_rows": int(len(combined)),
        "sample_rows": int(len(sample)),
        "sample_sha256": _sha256(sample_path),
        "ledger_inventory": inventory,
        "status_counts": _counts(combined, ["variant", "status"]),
        "window_counts": _counts(combined, ["variant", "execution_window", "status"]),
        "direction_counts": _counts(combined, ["variant", "direction", "status"]),
        "rejection_counts": _counts(
            combined,
            ["variant", "integrity_failure_scope", "rejection_reason"],
        ),
    }
    summary_path = args.report_root / "event_audit_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))


if __name__ == "__main__":
    main()
