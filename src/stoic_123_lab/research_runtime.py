from __future__ import annotations

import csv
import json
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

ResearchMode = Literal["screen", "validate", "certify", "legacy"]
ReviewScope = Literal["none", "candidate", "all"]

CANDIDATE_SCENARIOS = frozenset({"RTH_LONG_FULL"})
DECISION_STRESS_SCENARIOS = frozenset(
    {
        "RTH_LONG_FULL_COST_2T",
        "RTH_LONG_FULL_DELAY_1M",
        "RTH_LONG_FULL_DELAY_5M",
    }
)
SCREEN_SCENARIOS = frozenset({"RTH_LONG_FULL", "RTH_LONG_EMA_BREAK"})
VALIDATION_SCENARIOS = frozenset(
    {
        "RTH_LONG_FULL",
        "RTH_LONG_FULL_COST_2T",
        "RTH_LONG_FULL_DELAY_1M",
        "RTH_LONG_FULL_DELAY_5M",
        "RTH_LONG_EMA_BREAK",
        "RTH_LONG_EMA_BREAK_RETEST",
        "FULL_SESSION_LONG_FULL",
        "OVERNIGHT_ENTRY_LONG_FULL",
    }
)


@dataclass(frozen=True)
class ResearchPlan:
    mode: ResearchMode
    candidate_bootstrap_iterations: int
    diagnostic_bootstrap_iterations: int
    matched_control_replicates: int
    matched_control_candidates: tuple[str, ...]
    review_scope: ReviewScope
    write_ledgers: bool
    include_attribution: bool
    early_stop: bool
    exact_cost_repricing: bool
    scenarios: frozenset[str] | None

    def validate(self) -> None:
        if self.candidate_bootstrap_iterations < 0:
            raise ValueError("candidate bootstrap iterations cannot be negative")
        if self.diagnostic_bootstrap_iterations < 0:
            raise ValueError("diagnostic bootstrap iterations cannot be negative")
        if self.matched_control_replicates < 0:
            raise ValueError("matched control replicates cannot be negative")
        if self.review_scope not in {"none", "candidate", "all"}:
            raise ValueError(f"unsupported review scope: {self.review_scope}")

    def includes_scenario(self, name: str) -> bool:
        return self.scenarios is None or name in self.scenarios

    def bootstrap_iterations_for(self, name: str) -> int:
        if name in CANDIDATE_SCENARIOS:
            return self.candidate_bootstrap_iterations
        return self.diagnostic_bootstrap_iterations

    def should_review(self, name: str) -> bool:
        if self.review_scope == "all":
            return True
        if self.review_scope == "candidate":
            return name in CANDIDATE_SCENARIOS or name in DECISION_STRESS_SCENARIOS
        return False


def plan_for_mode(
    mode: ResearchMode,
    *,
    certify_iterations: int = 10_000,
) -> ResearchPlan:
    if certify_iterations <= 0:
        raise ValueError("certify_iterations must be positive")
    if mode == "screen":
        plan = ResearchPlan(
            mode=mode,
            candidate_bootstrap_iterations=0,
            diagnostic_bootstrap_iterations=0,
            matched_control_replicates=0,
            matched_control_candidates=(),
            review_scope="none",
            write_ledgers=False,
            include_attribution=False,
            early_stop=True,
            exact_cost_repricing=True,
            scenarios=SCREEN_SCENARIOS,
        )
    elif mode == "validate":
        plan = ResearchPlan(
            mode=mode,
            candidate_bootstrap_iterations=min(1_000, certify_iterations),
            diagnostic_bootstrap_iterations=0,
            matched_control_replicates=0,
            matched_control_candidates=(),
            review_scope="candidate",
            write_ledgers=True,
            include_attribution=True,
            early_stop=True,
            exact_cost_repricing=True,
            scenarios=VALIDATION_SCENARIOS,
        )
    elif mode == "certify":
        plan = ResearchPlan(
            mode=mode,
            candidate_bootstrap_iterations=certify_iterations,
            diagnostic_bootstrap_iterations=0,
            matched_control_replicates=50,
            matched_control_candidates=("RTH_LONG_FULL",),
            review_scope="all",
            write_ledgers=True,
            include_attribution=True,
            early_stop=False,
            exact_cost_repricing=True,
            scenarios=None,
        )
    elif mode == "legacy":
        plan = ResearchPlan(
            mode=mode,
            candidate_bootstrap_iterations=certify_iterations,
            diagnostic_bootstrap_iterations=certify_iterations,
            matched_control_replicates=50,
            matched_control_candidates=("RTH_LONG_EMA_BREAK", "RTH_LONG_FULL"),
            review_scope="all",
            write_ledgers=True,
            include_attribution=True,
            early_stop=False,
            exact_cost_repricing=False,
            scenarios=None,
        )
    else:
        raise ValueError(f"unsupported research mode: {mode}")
    plan.validate()
    return plan


def primary_futility_reason(summary: dict[str, object]) -> str | None:
    trades = int(summary.get("trades", 0))
    expectancy = float(summary.get("expectancy_r", float("nan")))
    net_r = float(summary.get("net_r", float("nan")))
    if trades < 30:
        return "PRIMARY_TRADE_COUNT_LT_30"
    if not (expectancy > 0 and net_r > 0):
        return "PRIMARY_NONPOSITIVE_EXPECTANCY_OR_NET_R"
    return None


@dataclass(frozen=True)
class TimingRecord:
    stage: str
    started_at_utc: str
    elapsed_seconds: float
    metadata: dict[str, object]


class StageTimer:
    def __init__(self) -> None:
        self._records: list[TimingRecord] = []

    @property
    def records(self) -> tuple[TimingRecord, ...]:
        return tuple(self._records)

    @contextmanager
    def measure(self, stage: str, **metadata: object) -> Iterator[None]:
        started = datetime.now(UTC)
        clock = time.perf_counter()
        try:
            yield
        finally:
            self._records.append(
                TimingRecord(
                    stage=stage,
                    started_at_utc=started.isoformat(),
                    elapsed_seconds=time.perf_counter() - clock,
                    metadata=dict(metadata),
                )
            )

    def write(self, directory: Path) -> None:
        directory.mkdir(parents=True, exist_ok=True)
        rows = [asdict(record) for record in self._records]
        (directory / "timings.json").write_text(
            json.dumps(rows, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        with (directory / "timings.csv").open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["stage", "started_at_utc", "elapsed_seconds", "metadata"],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(
                    {
                        "stage": row["stage"],
                        "started_at_utc": row["started_at_utc"],
                        "elapsed_seconds": row["elapsed_seconds"],
                        "metadata": json.dumps(row["metadata"], sort_keys=True),
                    }
                )
