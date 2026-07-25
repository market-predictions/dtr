from __future__ import annotations

import pandas as pd

from dtr_lab.strategies.asia_sweep.fx_ten_pair import match_controls
from dtr_lab.strategies.asia_sweep.fx_ten_pair_gate import build_decision


def _row(
    event_id: str,
    date: str,
    *,
    state: str,
    value: float,
    instrument: str = "EURUSD",
    factor: str = "usd_europe",
) -> dict[str, object]:
    return {
        "event_id": event_id,
        "instrument": instrument,
        "factor_block": factor,
        "trade_date": date,
        "state": state,
        "year": 2018,
        "weekday": 1,
        "time_bucket": 5,
        "range_percentile_60": 0.5,
        "breach_depth_range_fraction": 0.1,
        "reference_range": 1.0,
        "external_confluence": False,
        "reversal_return_60m_range_fraction": value,
        "is_primary_event": state == "REJECTION",
    }


def test_matching_uses_five_distinct_control_dates() -> None:
    rows = [_row("event", "2018-01-02", state="REJECTION", value=0.2)]
    for index in range(6):
        rows.append(
            _row(
                f"control-{index}",
                f"2018-02-{index + 1:02d}",
                state="ACCEPTANCE",
                value=0.01 * index,
            )
        )
    events, controls = match_controls(pd.DataFrame(rows))
    assert len(events) == 1
    assert len(controls) == 5
    assert controls["trade_date"].nunique() == 5
    assert abs(float(events.iloc[0]["effect"]) - (0.2 - 0.02)) < 1e-12


def test_matching_rejects_same_date_controls() -> None:
    rows = [_row("event", "2018-01-02", state="REJECTION", value=0.2)]
    for index in range(5):
        rows.append(
            _row(
                f"same-{index}",
                "2018-01-02",
                state="UNRESOLVED",
                value=0.0,
            )
        )
    events, controls = match_controls(pd.DataFrame(rows))
    assert events.empty
    assert controls.empty


def test_gate_requires_all_predicates(tmp_path) -> None:
    symbols = {
        "EURUSD": "usd_europe",
        "GBPUSD": "usd_europe",
        "USDCHF": "usd_europe",
        "AUDUSD": "usd_commodity",
        "NZDUSD": "usd_commodity",
        "USDCAD": "usd_commodity",
        "USDJPY": "jpy",
        "EURJPY": "jpy",
        "GBPJPY": "jpy",
        "EURGBP": "europe_cross",
    }
    for symbol, factor in symbols.items():
        directory = tmp_path / symbol
        directory.mkdir()
        rows = []
        for index in range(50):
            rows.append(
                {
                    "event_id": f"{symbol}-{index}",
                    "instrument": symbol,
                    "factor_block": factor,
                    "trade_date": (
                        f"2018-{(index % 12) + 1:02d}-{(index % 27) + 1:02d}"
                    ),
                    "event_return": 0.08,
                    "control_mean_return": 0.01,
                    "effect": 0.07,
                }
            )
        pd.DataFrame(rows).to_csv(directory / "matched_events.csv", index=False)
    decision, matched = build_decision(tmp_path)
    assert len(matched) == 500
    assert decision["passed"] is True
    assert (
        decision["decision"]
        == "PASS_DISCOVERY_AUTHORIZE_2020_2021_MECHANISM_VALIDATION"
    )
