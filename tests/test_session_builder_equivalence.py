from __future__ import annotations

import numpy as np
import pandas as pd
import pandas.testing as pdt

from dtr_lab.research.engine import SESSION_SPECS, build_session_table, resample_5m


def _legacy_build(one_minute: pd.DataFrame, bars: pd.DataFrame) -> pd.DataFrame:
    first_day = one_minute["timestamp"].min().normalize()
    last_day = one_minute["timestamp"].max().normalize()
    days = pd.date_range(first_day, last_day, freq="D")
    bar_times = bars["timestamp"].to_numpy(dtype="datetime64[ns]")
    one = one_minute.set_index("timestamp")
    rows: list[dict[str, object]] = []
    for day in days:
        for name, (start_hm, end_hm, break_hm) in SESSION_SPECS.items():
            start = day + pd.Timedelta(hours=start_hm[0], minutes=start_hm[1])
            end = day + pd.Timedelta(hours=end_hm[0], minutes=end_hm[1])
            break_end = day + pd.Timedelta(hours=break_hm[0], minutes=break_hm[1])
            if break_end <= end:
                break_end += pd.Timedelta(days=1)
            window = one.loc[(one.index >= start) & (one.index < end)]
            if len(window) < 20:
                continue
            i0 = int(np.searchsorted(bar_times, np.datetime64(end), side="left"))
            i1 = int(np.searchsorted(bar_times, np.datetime64(break_end), side="left"))
            if i0 >= len(bars) or i1 <= i0:
                continue
            high = float(window["high"].max())
            low = float(window["low"].min())
            rows.append(
                {
                    "session": name,
                    "session_date": day,
                    "range_start": start,
                    "range_end": end,
                    "break_end": break_end,
                    "range_high": high,
                    "range_low": low,
                    "range_size": high - low,
                    "post_start_index": i0,
                    "post_end_index": min(i1, len(bars)),
                    "weekday": int(day.weekday()),
                }
            )
    return pd.DataFrame(rows)


def test_searchsorted_session_builder_matches_legacy_windows() -> None:
    timestamps = pd.date_range("2025-01-06 00:00", "2025-01-08 23:59", freq="1min")
    values = np.arange(len(timestamps), dtype=float)
    one = pd.DataFrame(
        {
            "timestamp": timestamps,
            "open": 100.0 + values * 0.001,
            "high": 100.5 + values * 0.001,
            "low": 99.5 + values * 0.001,
            "close": 100.1 + values * 0.001,
            "volume": 1.0 + values % 10,
        }
    )
    # Remove edge and interior bars to exercise search boundaries and incomplete windows.
    removed = pd.to_datetime(["2025-01-06 08:12", "2025-01-07 01:45"])
    one = one.loc[~one["timestamp"].isin(removed)].reset_index(drop=True)
    bars = resample_5m(one)
    actual = build_session_table(one, bars).reset_index(drop=True)
    expected = _legacy_build(one, bars).reset_index(drop=True)
    pdt.assert_frame_equal(actual.loc[:, expected.columns], expected, check_dtype=True)
