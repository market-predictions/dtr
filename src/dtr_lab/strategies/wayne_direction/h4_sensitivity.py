from __future__ import annotations

import math

import numpy as np
import pandas as pd

_HEALTHY = {
    "BULL": {"BULL_EXPANDING", "BULL_STABLE"},
    "BEAR": {"BEAR_EXPANDING", "BEAR_STABLE"},
}
_TARGETS = {
    "BULL": ("M4", "R2"),
    "BEAR": ("M1", "S2"),
}


def classify_h4_relation(
    side: str,
    h4_direction: str | float | None,
    health_state: str | float | None,
) -> str:
    if side not in _HEALTHY:
        raise ValueError(f"unsupported zone side: {side}")
    direction = "NONE" if pd.isna(h4_direction) else str(h4_direction)
    health = "WARMUP" if pd.isna(health_state) else str(health_state)
    if direction == side:
        return "ALIGNED_HEALTHY" if health in _HEALTHY[side] else "ALIGNED_UNHEALTHY"
    if direction in {"NONE", "AMBIGUOUS_SHOCK", "WARMUP"}:
        return "NO_H4_DIRECTION"
    return "OPPOSITE_H4_DIRECTION"


def classify_d1_relation(
    side: str,
    d1_direction: str | float | None,
) -> str:
    if side not in _HEALTHY:
        raise ValueError(f"unsupported zone side: {side}")
    direction = "NONE" if pd.isna(d1_direction) else str(d1_direction)
    if direction == side:
        return "D1_ALIGNED"
    if direction in {"NONE", "AMBIGUOUS_SHOCK", "WARMUP"}:
        return "D1_NONE"
    return "D1_OPPOSED"


def _asof_rows(
    timestamps: pd.Series,
    frame: pd.DataFrame,
    columns: list[str],
    prefix: str,
) -> pd.DataFrame:
    if not isinstance(frame.index, pd.DatetimeIndex) or frame.index.tz is None:
        raise ValueError("as-of source must use a timezone-aware DatetimeIndex")
    missing = sorted(set(columns) - set(frame.columns))
    if missing:
        raise ValueError(f"as-of source missing columns: {missing}")
    left = pd.DataFrame({"sample_timestamp": pd.to_datetime(timestamps, utc=True)})
    right = frame.loc[:, columns].sort_index().reset_index(names="source_timestamp")
    right = right.rename(columns={column: f"{prefix}_{column}" for column in columns})
    return pd.merge_asof(
        left.sort_values("sample_timestamp"),
        right,
        left_on="sample_timestamp",
        right_on="source_timestamp",
        direction="backward",
        allow_exact_matches=True,
    ).sort_index()


def _month_open_rows(
    daily_bars: pd.DataFrame,
    monthly_context: pd.DataFrame,
) -> pd.DataFrame:
    if not daily_bars.index.equals(monthly_context.index):
        raise ValueError("daily bars and monthly context indexes must match")
    if "bar_start_utc" not in daily_bars.columns:
        raise ValueError("daily bars missing bar_start_utc")
    required = {
        "month_id",
        "month_open",
        "month_open_location",
        "M1",
        "M2",
        "M3",
        "M4",
        "R1",
        "R2",
        "S1",
        "S2",
    }
    missing = sorted(required - set(monthly_context.columns))
    if missing:
        raise ValueError(f"monthly context missing columns: {missing}")
    joined = daily_bars.loc[:, ["bar_start_utc"]].join(
        monthly_context.loc[:, sorted(required)]
    )
    rows = joined.groupby("month_id", sort=True).first().reset_index()
    rows["month_open_timestamp"] = pd.to_datetime(rows["bar_start_utc"], utc=True)
    return rows.drop(columns="bar_start_utc")


def _first_true(mask: np.ndarray) -> int | None:
    positions = np.flatnonzero(mask)
    return None if len(positions) == 0 else int(positions[0])


def build_h4_monthly_attribution(
    daily_bars: pd.DataFrame,
    monthly_context: pd.DataFrame,
    d1_structure: pd.DataFrame,
    h4_structure: pd.DataFrame,
    h4_health: pd.DataFrame,
) -> pd.DataFrame:
    if not daily_bars.index.equals(d1_structure.index):
        raise ValueError("daily bars and D1 structure indexes must match")
    opens = _month_open_rows(daily_bars, monthly_context)

    d1_sample = _asof_rows(
        opens["month_open_timestamp"],
        d1_structure,
        ["confirmed_direction"],
        "d1",
    )
    h4_sample = _asof_rows(
        opens["month_open_timestamp"],
        h4_structure,
        ["confirmed_direction"],
        "h4",
    )
    health_sample = _asof_rows(
        opens["month_open_timestamp"],
        h4_health,
        ["health_state"],
        "h4",
    )
    opens["d1_source_timestamp"] = d1_sample["source_timestamp"].to_numpy()
    opens["d1_direction"] = d1_sample["d1_confirmed_direction"].to_numpy()
    opens["h4_source_timestamp"] = h4_sample["source_timestamp"].to_numpy()
    opens["h4_direction"] = h4_sample["h4_confirmed_direction"].to_numpy()
    opens["h4_health_timestamp"] = health_sample["source_timestamp"].to_numpy()
    opens["h4_health_state"] = health_sample["h4_health_state"].to_numpy()

    daily = daily_bars.join(monthly_context[["month_id"]])
    rows: list[dict[str, object]] = []
    for month in opens.itertuples(index=False):
        if month.month_open_location == "BUY_ZONE":
            side = "BULL"
            comparator = np.greater_equal
            path_column = "high"
        elif month.month_open_location == "SELL_ZONE":
            side = "BEAR"
            comparator = np.less_equal
            path_column = "low"
        else:
            continue
        path = daily.loc[daily["month_id"].eq(month.month_id)].copy()
        values = path[path_column].to_numpy(dtype=float)
        h4_relation = classify_h4_relation(
            side,
            month.h4_direction,
            month.h4_health_state,
        )
        d1_relation = classify_d1_relation(side, month.d1_direction)
        for target_name in _TARGETS[side]:
            target = float(getattr(month, target_name))
            target_pos = _first_true(comparator(values, target))
            rows.append(
                {
                    "month_id": int(month.month_id),
                    "year": int(month.month_id) // 100,
                    "month_open_timestamp": month.month_open_timestamp,
                    "side": side,
                    "month_open": float(month.month_open),
                    "month_open_location": month.month_open_location,
                    "d1_source_timestamp": month.d1_source_timestamp,
                    "d1_direction": month.d1_direction,
                    "d1_relation": d1_relation,
                    "h4_source_timestamp": month.h4_source_timestamp,
                    "h4_direction": month.h4_direction,
                    "h4_health_timestamp": month.h4_health_timestamp,
                    "h4_health_state": month.h4_health_state,
                    "h4_relation": h4_relation,
                    "target_name": target_name,
                    "target": target,
                    "reached_by_month_end": target_pos is not None,
                    "target_pos": target_pos,
                    "days_to_target": target_pos if target_pos is not None else math.nan,
                    "observed_days": int(len(path)),
                }
            )
    return pd.DataFrame(rows)
