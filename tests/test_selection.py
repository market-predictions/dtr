from __future__ import annotations

import pandas as pd

from dtr_lab.research.selection import (
    align_candidate_returns,
    bootstrap_reselection,
    candidate_stream_hashes,
    duplicate_stream_groups,
    familywise_selection_test,
)


def _trades() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "candidate_id": ["A", "A", "A", "B", "B", "C", "C", "C"],
            "session_date": pd.to_datetime(
                [
                    "2025-01-02",
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-02",
                    "2025-01-03",
                    "2025-01-02",
                    "2025-01-02",
                    "2025-01-03",
                ]
            ),
            "session": [
                "LONDON",
                "NEW_YORK",
                "LONDON",
                "LONDON",
                "NEW_YORK",
                "LONDON",
                "NEW_YORK",
                "LONDON",
            ],
            "pnl_r": [1.0, 0.5, 1.0, -0.5, 0.1, 1.0, 0.5, 1.0],
        }
    )


def test_align_candidate_returns_assigns_zero_for_no_trade() -> None:
    matrix = align_candidate_returns(
        _trades(), candidate_ids=["A", "B", "C"], observation_unit="session"
    )
    assert list(matrix.columns) == ["A", "B", "C"]
    assert matrix.loc[(pd.Timestamp("2025-01-02"), "NEW_YORK"), "B"] == 0.0
    assert matrix.loc[(pd.Timestamp("2025-01-03"), "NEW_YORK"), "A"] == 0.0


def test_calendar_date_alignment_sums_sessions() -> None:
    matrix = align_candidate_returns(_trades(), observation_unit="date")
    assert matrix.loc[pd.Timestamp("2025-01-02"), "A"] == 1.5
    assert matrix.loc[pd.Timestamp("2025-01-02"), "C"] == 1.5


def test_stream_hashes_and_duplicate_detection_are_deterministic() -> None:
    matrix = align_candidate_returns(_trades(), observation_unit="session")
    first = candidate_stream_hashes(matrix)
    second = candidate_stream_hashes(matrix.copy())
    assert first == second
    assert duplicate_stream_groups(matrix) == [["A", "C"]]


def test_familywise_test_is_deterministic() -> None:
    matrix = align_candidate_returns(_trades(), observation_unit="session")
    first = familywise_selection_test(
        matrix, selected_candidate="A", iterations=1_000, seed=13
    )
    second = familywise_selection_test(
        matrix, selected_candidate="A", iterations=1_000, seed=13
    )
    assert first == second
    assert 0.0 < first.max_t_p_value <= 1.0
    assert 0.0 < first.best_mean_p_value <= 1.0


def test_bootstrap_reselection_reports_winner_instability() -> None:
    matrix = align_candidate_returns(_trades(), observation_unit="session")
    result = bootstrap_reselection(
        matrix, selected_candidate="A", iterations=1_000, seed=17
    )
    assert result.frequencies["A"] + result.frequencies["B"] + result.frequencies["C"] == 1.0
    assert result.selected_frequency < 1.0
    assert result.winner_change_probability > 0.0
    assert result.effective_selected_candidates >= 1.0
