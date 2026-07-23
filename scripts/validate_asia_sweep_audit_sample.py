from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile

import numpy as np
import pandas as pd
import yaml

_FORBIDDEN_RESULT_TOKENS = (
    "pnl",
    "return",
    "realized",
    "exit_price",
    "exit_reason",
    "mfe",
    "mae",
)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _timestamp(value: object) -> pd.Timestamp:
    return pd.Timestamp(value)


def _wall_timestamp(
    trade_date: object,
    hour: int,
    minute: int,
    timezone: str,
) -> pd.Timestamp:
    day = pd.Timestamp(str(trade_date)[:10])
    naive = pd.Timestamp(
        year=day.year,
        month=day.month,
        day=day.day,
        hour=hour,
        minute=minute,
    )
    return naive.tz_localize(timezone, ambiguous="raise", nonexistent="raise")


def _window_bounds(
    row: pd.Series,
    windows: dict[str, tuple[tuple[int, int], tuple[int, int]]],
    timezone: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    name = str(row["execution_window"])
    if name not in windows:
        raise ValueError(f"Unknown execution window: {name}")
    start_clock, end_clock = windows[name]
    start = _wall_timestamp(row["trade_date"], *start_clock, timezone)
    end = _wall_timestamp(row["trade_date"], *end_clock, timezone)
    if end <= start:
        next_date = pd.Timestamp(str(row["trade_date"])[:10]) + pd.DateOffset(days=1)
        end = _wall_timestamp(next_date, *end_clock, timezone)
    return start, end


def _maximum_false_run(values: np.ndarray) -> int:
    if not len(values):
        return 0
    inactive = ~values.astype(bool)
    if not bool(inactive.any()):
        return 0
    changes = np.diff(np.r_[False, inactive, False].astype(np.int8))
    starts = np.flatnonzero(changes == 1)
    ends = np.flatnonzero(changes == -1)
    return int((ends - starts).max())


def _close(left: object, right: object, tolerance: float = 1e-9) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    if pd.isna(left) or pd.isna(right):
        return False
    left_value = float(left)
    right_value = float(right)
    scale = max(1.0, abs(left_value), abs(right_value))
    return abs(left_value - right_value) <= tolerance * scale


def _as_bool(value: object) -> bool:
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1"}:
            return True
        if normalized in {"false", "0"}:
            return False
        raise ValueError(f"Cannot interpret boolean value: {value}")
    return bool(value)


def _load_manifest(path: Path) -> dict[str, object]:
    manifest = yaml.safe_load(path.read_text())
    if not isinstance(manifest, dict):
        raise ValueError("Manifest must be a mapping")
    return manifest


def _manifest_windows(
    manifest: dict[str, object],
) -> dict[str, tuple[tuple[int, int], tuple[int, int]]]:
    windows: dict[str, tuple[tuple[int, int], tuple[int, int]]] = {}
    for item in manifest["strategy"]["execution_windows"]:
        start_hour, start_minute = (int(value) for value in item["start"].split(":"))
        end_hour, end_minute = (int(value) for value in item["end"].split(":"))
        windows[str(item["name"])] = (
            (start_hour, start_minute),
            (end_hour, end_minute),
        )
    return windows


def _source_bounds(
    sample: pd.DataFrame,
    windows: dict[str, tuple[tuple[int, int], tuple[int, int]]],
    timezone: str,
) -> tuple[pd.Timestamp, pd.Timestamp]:
    starts = [_timestamp(value) for value in sample["asia_start"]]
    ends = [_window_bounds(row, windows, timezone)[1] for _, row in sample.iterrows()]
    start = min(starts).tz_convert("UTC")
    end = max(ends).tz_convert("UTC")
    return start, end


def _load_source(
    source_zip: Path,
    manifest: dict[str, object],
    sample: pd.DataFrame,
) -> pd.DataFrame:
    dataset = manifest["dataset"]
    schema = dataset["schema"]
    source_timezone = str(dataset["source_timezone"])
    session_timezone = str(dataset["session_timezone"])
    windows = _manifest_windows(manifest)
    range_start, range_end = _source_bounds(sample, windows, session_timezone)
    required = {
        str(schema["timestamp_column"]),
        *[str(column) for column in schema["required_columns"]],
    }

    with ZipFile(source_zip) as archive:
        members = [name for name in archive.namelist() if name.lower().endswith(".csv")]
        if len(members) != 1:
            raise ValueError(f"Expected exactly one CSV member, found {members}")
        with archive.open(members[0]) as handle:
            header = pd.read_csv(handle, nrows=0)
    missing = required.difference(header.columns)
    if missing:
        raise ValueError(f"Source missing required columns: {sorted(missing)}")

    use_columns = [
        str(schema["timestamp_column"]),
        "open",
        "high",
        "low",
        "close",
        "volume",
        str(schema["activity_column"]),
    ]
    dtypes = {
        "open": "float64",
        "high": "float64",
        "low": "float64",
        "close": "float64",
        "volume": "float64",
        str(schema["activity_column"]): "int8",
    }
    parts: list[pd.DataFrame] = []
    with ZipFile(source_zip) as archive:
        with archive.open(members[0]) as handle:
            chunks = pd.read_csv(
                handle,
                usecols=use_columns,
                dtype=dtypes,
                chunksize=200_000,
            )
            for chunk in chunks:
                timestamps = pd.to_datetime(
                    chunk[str(schema["timestamp_column"])],
                    format=schema.get("timestamp_format"),
                    errors="raise",
                    utc=source_timezone.upper() == "UTC",
                )
                if timestamps.dt.tz is None:
                    timestamps = timestamps.dt.tz_localize(
                        source_timezone,
                        ambiguous="raise",
                        nonexistent="raise",
                    )
                else:
                    timestamps = timestamps.dt.tz_convert(source_timezone)
                mask = (timestamps >= range_start) & (timestamps < range_end)
                if not bool(mask.any()):
                    continue
                selected = chunk.loc[mask].copy()
                selected["timestamp_source"] = timestamps.loc[mask]
                selected["timestamp"] = timestamps.loc[mask].dt.tz_convert(
                    session_timezone
                )
                parts.append(selected)

    if not parts:
        raise ValueError("No source rows overlap the audit sample")
    source = pd.concat(parts, ignore_index=True)
    source = source.sort_values("timestamp").reset_index(drop=True)
    if bool(source["timestamp"].duplicated(keep=False).any()):
        raise ValueError("Source contains duplicate timestamps in the audit range")
    return source


def _resample_five_minutes(
    source: pd.DataFrame,
    activity_column: str,
) -> pd.DataFrame:
    indexed = source.set_index("timestamp").sort_index()
    bars = (
        indexed.resample("5min", label="left", closed="left")
        .agg(
            open=("open", "first"),
            high=("high", "max"),
            low=("low", "min"),
            close=("close", "last"),
            volume=("volume", "sum"),
            source_bars=("close", "count"),
            active_minutes=(activity_column, "sum"),
        )
        .dropna(subset=["open", "high", "low", "close"])
        .reset_index()
    )
    bars["bar_end"] = bars["timestamp"] + pd.Timedelta(minutes=5)
    bodies = (bars["close"] - bars["open"]).abs()
    bars["causal_body_median"] = bodies.shift(1).rolling(
        20,
        min_periods=20,
    ).median()
    return bars


def _morphology(row: pd.Series, direction: int) -> tuple[float, float]:
    span = float(row["high"] - row["low"])
    if span <= 0:
        return 0.0, 0.5
    if direction > 0:
        wick = max(0.0, min(row["open"], row["close"]) - row["low"]) / span
        close_location = (row["close"] - row["low"]) / span
    else:
        wick = max(0.0, row["high"] - max(row["open"], row["close"])) / span
        close_location = (row["high"] - row["close"]) / span
    return float(wick), float(close_location)


def _failed_retest_entry(
    bars: pd.DataFrame,
    sweep_position: int,
    direction: int,
    sweep_extreme: float,
    asia_level: float,
    max_bars: int,
    band: float,
) -> int | None:
    end = min(len(bars), sweep_position + max_bars + 1)
    reaction_level: float | None = None
    reaction_confirmed_at: int | None = None
    retest_seen = False
    for position in range(sweep_position + 2, end):
        candidate = position - 1
        previous = bars.iloc[candidate - 1]
        middle = bars.iloc[candidate]
        following = bars.iloc[position]
        if reaction_level is None:
            if direction > 0:
                pivot = (
                    middle["high"] > previous["high"]
                    and middle["high"] > following["high"]
                )
                if pivot:
                    reaction_level = float(middle["high"])
                    reaction_confirmed_at = position
            else:
                pivot = (
                    middle["low"] < previous["low"]
                    and middle["low"] < following["low"]
                )
                if pivot:
                    reaction_level = float(middle["low"])
                    reaction_confirmed_at = position
            continue
        if reaction_confirmed_at is None or position <= reaction_confirmed_at:
            continue
        current = bars.iloc[position]
        if not retest_seen:
            if direction > 0:
                retest_seen = (
                    current["low"] <= asia_level + band
                    and current["low"] > sweep_extreme
                )
            else:
                retest_seen = (
                    current["high"] >= asia_level - band
                    and current["high"] < sweep_extreme
                )
            continue
        broke = (
            current["close"] > reaction_level
            if direction > 0
            else current["close"] < reaction_level
        )
        if broke:
            return position
    return None


def _append_error(errors: list[str], condition: bool, label: str) -> None:
    if condition:
        errors.append(label)


def _validate_event(
    row: pd.Series,
    source: pd.DataFrame,
    bars: pd.DataFrame,
    manifest: dict[str, object],
) -> list[str]:
    dataset = manifest["dataset"]
    strategy = manifest["strategy"]
    activity_gate = dataset["activity_gate"]
    activity_column = str(dataset["schema"]["activity_column"])
    timezone = str(dataset["session_timezone"])
    windows = _manifest_windows(manifest)
    tick_size = float(dataset["tick_size"])
    asia_start = _timestamp(row["asia_start"])
    asia_end = _timestamp(row["asia_end"])
    window_start, window_end = _window_bounds(row, windows, timezone)
    asia = source[
        (source["timestamp"] >= asia_start) & (source["timestamp"] < asia_end)
    ]
    execution = source[
        (source["timestamp"] >= window_start)
        & (source["timestamp"] < window_end)
    ]
    window_bars = bars[
        (bars["timestamp"] >= window_start) & (bars["timestamp"] < window_end)
    ].copy().reset_index(drop=True)
    errors: list[str] = []

    expected_asia = int(
        (asia_end.tz_convert("UTC") - asia_start.tz_convert("UTC")).total_seconds()
        / 60
    )
    expected_execution = int(
        (
            window_end.tz_convert("UTC") - window_start.tz_convert("UTC")
        ).total_seconds()
        / 60
    )
    _append_error(errors, len(asia) != expected_asia, "asia_minute_grid")
    _append_error(errors, len(execution) != expected_execution, "execution_minute_grid")

    asia_activity = asia[activity_column].to_numpy() > 0
    execution_activity = execution[activity_column].to_numpy() > 0
    asia_active = int(asia_activity.sum())
    execution_active = int(execution_activity.sum())
    asia_run = _maximum_false_run(asia_activity)
    execution_run = _maximum_false_run(execution_activity)
    activity_limit = int(activity_gate["maximum_consecutive_zero_volume_minutes"])
    minimum_active = int(activity_gate["minimum_positive_volume_minutes"])
    asia_eligible = asia_active >= minimum_active and asia_run <= activity_limit
    execution_eligible = (
        execution_active >= minimum_active and execution_run <= activity_limit
    )
    metric_checks = {
        "asia_active_minutes": asia_active,
        "asia_inactive_minutes": len(asia) - asia_active,
        "asia_max_inactive_run": asia_run,
        "execution_active_minutes": execution_active,
        "execution_inactive_minutes": len(execution) - execution_active,
        "execution_max_inactive_run": execution_run,
    }
    for column, expected in metric_checks.items():
        _append_error(errors, not _close(row[column], expected), column)
    _append_error(
        errors,
        _as_bool(row["asia_activity_eligible"]) != asia_eligible,
        "asia_activity_eligible",
    )
    _append_error(
        errors,
        _as_bool(row["execution_activity_eligible"]) != execution_eligible,
        "execution_activity_eligible",
    )

    if not asia_eligible:
        expected_reason = (
            "no_positive_volume_activity"
            if asia_active < minimum_active
            else "stale_quote_run_exceeded"
        )
        _append_error(errors, row["status"] != "INELIGIBLE", "ineligible_status")
        _append_error(
            errors,
            row["rejection_reason"] != expected_reason,
            "ineligible_reason",
        )
        _append_error(
            errors,
            row["integrity_failure_scope"] != "asia_range",
            "ineligible_scope",
        )
        return errors

    asia_high = float(asia["high"].max())
    asia_low = float(asia["low"].min())
    _append_error(errors, not _close(row["asia_high"], asia_high), "asia_high")
    _append_error(errors, not _close(row["asia_low"], asia_low), "asia_low")
    minimum_depth = int(strategy["min_sweep_ticks"]) * tick_size
    upper = window_bars["high"] - asia_high >= minimum_depth
    lower = asia_low - window_bars["low"] >= minimum_depth
    sweep_positions = np.flatnonzero((upper | lower).to_numpy())
    if not len(sweep_positions):
        _append_error(errors, row["status"] != "NO_SWEEP", "no_sweep_status")
        return errors

    sweep_position = int(sweep_positions[0])
    sweep_bar = window_bars.iloc[sweep_position]
    upper_sweep = bool(upper.iloc[sweep_position])
    lower_sweep = bool(lower.iloc[sweep_position])
    _append_error(
        errors,
        _timestamp(row["first_sweep_timestamp"]) != sweep_bar["timestamp"],
        "first_sweep_timestamp",
    )
    if upper_sweep and lower_sweep:
        _append_error(errors, row["status"] != "REJECTED", "ambiguous_status")
        _append_error(
            errors,
            row["rejection_reason"] != "ambiguous_double_sweep",
            "ambiguous_reason",
        )
        return errors

    direction = 1 if lower_sweep else -1
    swept_side = "LOW" if direction > 0 else "HIGH"
    sweep_extreme = float(
        sweep_bar["low"] if direction > 0 else sweep_bar["high"]
    )
    depth = (
        asia_low - sweep_extreme
        if direction > 0
        else sweep_extreme - asia_high
    )
    _append_error(errors, int(row["direction"]) != direction, "direction")
    _append_error(errors, row["swept_side"] != swept_side, "swept_side")
    numeric_checks = {
        "sweep_extreme": sweep_extreme,
        "sweep_depth_points": depth,
        "sweep_depth_ticks": depth / tick_size,
        "sweep_bar_open": sweep_bar["open"],
        "sweep_bar_high": sweep_bar["high"],
        "sweep_bar_low": sweep_bar["low"],
        "sweep_bar_close": sweep_bar["close"],
    }
    for column, expected in numeric_checks.items():
        _append_error(errors, not _close(row[column], expected), column)

    reclaim = (
        sweep_bar["close"] >= asia_low
        if direction > 0
        else sweep_bar["close"] <= asia_high
    )
    wick_ratio, close_location = _morphology(sweep_bar, direction)
    _append_error(
        errors,
        _as_bool(row["closed_back_inside"]) != bool(reclaim),
        "closed_back_inside",
    )
    _append_error(errors, not _close(row["wick_ratio"], wick_ratio), "wick_ratio")
    _append_error(
        errors,
        not _close(row["close_location_value"], close_location),
        "close_location_value",
    )
    if not reclaim:
        _append_error(errors, row["status"] != "REJECTED", "reclaim_status")
        _append_error(
            errors,
            row["rejection_reason"] != "no_same_bar_reclaim",
            "reclaim_reason",
        )
        return errors

    variant = str(row["variant"])
    entry_position = sweep_position
    if variant == "AS_B_WICK_QUALIFIED":
        morphology_failed = (
            wick_ratio < float(strategy["wick_ratio_min"])
            or close_location < float(strategy["close_location_min"])
        )
        if morphology_failed:
            _append_error(errors, row["status"] != "REJECTED", "morphology_status")
            _append_error(
                errors,
                row["rejection_reason"] != "morphology_failed",
                "morphology_reason",
            )
            return errors
    elif variant == "AS_C_DISPLACEMENT":
        midpoint = float(sweep_bar["high"] + sweep_bar["low"]) / 2.0
        found: int | None = None
        delay: int | None = None
        final = min(
            len(window_bars),
            sweep_position + int(strategy["displacement_max_bars"]) + 1,
        )
        for position in range(sweep_position + 1, final):
            candidate = window_bars.iloc[position]
            body_reference = float(candidate["causal_body_median"])
            if not np.isfinite(body_reference) or body_reference <= 0:
                continue
            body = abs(float(candidate["close"] - candidate["open"]))
            directional = (
                candidate["close"] > candidate["open"]
                if direction > 0
                else candidate["close"] < candidate["open"]
            )
            midpoint_pass = (
                candidate["close"] > midpoint
                if direction > 0
                else candidate["close"] < midpoint
            )
            inside = (
                candidate["close"] >= asia_low
                if direction > 0
                else candidate["close"] <= asia_high
            )
            qualifies = (
                directional
                and midpoint_pass
                and inside
                and body
                >= float(strategy["displacement_body_mult"]) * body_reference
            )
            if qualifies:
                found = position
                delay = position - sweep_position
                break
        if found is None:
            _append_error(errors, row["status"] != "REJECTED", "displacement_status")
            _append_error(
                errors,
                row["rejection_reason"] != "no_displacement",
                "displacement_reason",
            )
            return errors
        entry_position = found
        _append_error(
            errors,
            not _as_bool(row["displacement_present"]),
            "displacement_present",
        )
        _append_error(
            errors,
            int(row["displacement_delay_bars"]) != delay,
            "displacement_delay_bars",
        )
    elif variant == "AS_D_FAILED_RETEST":
        asia_level = asia_low if direction > 0 else asia_high
        found = _failed_retest_entry(
            window_bars,
            sweep_position,
            direction,
            sweep_extreme,
            asia_level,
            int(strategy["failed_retest_max_bars"]),
            int(strategy["retest_band_ticks"]) * tick_size,
        )
        if found is None:
            _append_error(errors, row["status"] != "REJECTED", "failed_retest_status")
            _append_error(
                errors,
                row["rejection_reason"] != "no_failed_retest",
                "failed_retest_reason",
            )
            return errors
        entry_position = found
        _append_error(
            errors,
            not _as_bool(row["failed_retest_present"]),
            "failed_retest_present",
        )

    entry_bar = window_bars.iloc[entry_position]
    entry_timestamp = entry_bar["bar_end"]
    if entry_timestamp >= window_end:
        _append_error(errors, row["status"] != "REJECTED", "late_entry_status")
        _append_error(
            errors,
            row["rejection_reason"] != "entry_at_or_after_window_end",
            "late_entry_reason",
        )
        _append_error(
            errors,
            _timestamp(row["entry_timestamp"]) != entry_timestamp,
            "late_entry_timestamp",
        )
        return errors

    entry = float(entry_bar["close"])
    stop = (
        sweep_extreme - int(strategy["stop_buffer_ticks"]) * tick_size
        if direction > 0
        else sweep_extreme + int(strategy["stop_buffer_ticks"]) * tick_size
    )
    risk = entry - stop if direction > 0 else stop - entry
    if risk <= tick_size:
        _append_error(errors, row["status"] != "REJECTED", "risk_status")
        _append_error(
            errors,
            row["rejection_reason"] != "nonpositive_or_too_small_risk",
            "risk_reason",
        )
        return errors

    target = entry + direction * risk * float(strategy["target_rr"])
    _append_error(errors, row["status"] != "SIGNAL", "signal_status")
    _append_error(
        errors,
        _timestamp(row["entry_timestamp"]) != entry_timestamp,
        "entry_timestamp",
    )
    for column, expected in {
        "entry_price_raw": entry,
        "stop_price_raw": stop,
        "target_price_raw": target,
    }.items():
        _append_error(errors, not _close(row[column], expected), column)
    return errors


def _evidence_frame(
    sample: pd.DataFrame,
    bars: pd.DataFrame,
    manifest: dict[str, object],
) -> pd.DataFrame:
    windows = _manifest_windows(manifest)
    timezone = str(manifest["dataset"]["session_timezone"])
    output: list[pd.DataFrame] = []
    identity_columns = [
        "stable_sample_key",
        "instrument",
        "trade_date",
        "execution_window",
        "variant",
        "status",
        "rejection_reason",
        "direction_label",
        "asia_high",
        "asia_low",
        "first_sweep_timestamp",
        "entry_timestamp",
    ]
    for _, event in sample.iterrows():
        asia_start = _timestamp(event["asia_start"])
        asia_end = _timestamp(event["asia_end"])
        window_start, window_end = _window_bounds(event, windows, timezone)
        segments = (
            ("ASIA_RANGE", asia_start, asia_end),
            ("EXECUTION_WINDOW", window_start, window_end),
        )
        for segment, start, end in segments:
            selected = bars[
                (bars["timestamp"] >= start) & (bars["timestamp"] < end)
            ].copy()
            selected.insert(0, "segment", segment)
            for column in reversed(identity_columns):
                selected.insert(0, column, event[column])
            output.append(selected)
    if not output:
        raise ValueError("No five-minute evidence was produced")
    evidence = pd.concat(output, ignore_index=True)
    return evidence.drop(columns=["causal_body_median"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-zip", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--sample", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()

    manifest = _load_manifest(args.manifest)
    sample = pd.read_csv(args.sample)
    forbidden = [
        column
        for column in sample.columns
        if any(token in column.lower() for token in _FORBIDDEN_RESULT_TOKENS)
    ]
    if forbidden:
        raise ValueError(f"Audit sample contains prohibited result columns: {forbidden}")
    source = _load_source(args.source_zip, manifest, sample)
    activity_column = str(manifest["dataset"]["schema"]["activity_column"])
    bars = _resample_five_minutes(source, activity_column)

    records: list[dict[str, object]] = []
    for _, row in sample.iterrows():
        errors = _validate_event(row, source, bars, manifest)
        records.append(
            {
                "stable_sample_key": row["stable_sample_key"],
                "instrument": row["instrument"],
                "trade_date": row["trade_date"],
                "execution_window": row["execution_window"],
                "variant": row["variant"],
                "status": row["status"],
                "rejection_reason": row["rejection_reason"],
                "validation_passed": not errors,
                "validation_errors": "|".join(errors),
            }
        )
    validations = pd.DataFrame(records)
    args.output_root.mkdir(parents=True, exist_ok=True)
    validation_path = args.output_root / "independent_validation_50.csv"
    validations.to_csv(validation_path, index=False)

    evidence = _evidence_frame(sample, bars, manifest)
    evidence_path = args.output_root / "manual_audit_five_minute_evidence_50.csv"
    evidence.to_csv(evidence_path, index=False)

    error_count = int((~validations["validation_passed"]).sum())
    summary = {
        "instrument": str(manifest["dataset"]["instrument"]),
        "strategy_id": str(manifest["strategy_id"]),
        "purpose": "clean-room event reconstruction and private OHLC audit evidence",
        "validator": "independent_spec_reimplementation_v1",
        "sample_rows": int(len(sample)),
        "validation_errors": error_count,
        "all_events_valid": error_count == 0,
        "sample_sha256": _sha256(args.sample),
        "validation_sha256": _sha256(validation_path),
        "evidence_rows": int(len(evidence)),
        "evidence_sha256": _sha256(evidence_path),
        "source_zip_sha256": _sha256(args.source_zip),
        "pnl_calculated": False,
        "execution_simulated": False,
    }
    summary_path = args.output_root / "independent_validation_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str) + "\n")
    print(json.dumps(summary, indent=2, default=str))
    if error_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
