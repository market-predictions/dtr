from __future__ import annotations

from pathlib import Path

import pytest

from stoic_123_lab.config import SequenceConfig
from stoic_123_lab.research_batch import (
    VariationSpec,
    apply_variation,
    detection_signature,
    group_variations_by_detection,
    load_batch_design,
)


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def test_discovery_batch_contract_loads_and_applies_variations(tmp_path) -> None:
    path = _write(
        tmp_path / "batch.yaml",
        """
study_id: TEST-BATCH
status: DISCOVERY_ONLY
source_partition: primary_forward
promotion_authorized: false
holdout_access_authorized: false
variations:
  - id: baseline
    description: Baseline
    overrides: {}
  - id: wider_base
    description: Wider base
    overrides:
      base_max_bars: 10
""".strip()
        + "\n",
    )
    design = load_batch_design(path, allowed_partitions={"primary_forward"})
    assert design.study_id == "TEST-BATCH"
    assert len(design.variations) == 2
    base = SequenceConfig(arm_id="BASE", description="base")
    varied = apply_variation(base, design.variations[1])
    assert varied.base_max_bars == 10
    assert varied.arm_id == "BASE__BATCH__wider_base"


def test_execution_only_variations_share_detection_signature() -> None:
    base = SequenceConfig(arm_id="BASE", description="base")
    variations = (
        VariationSpec("cost_1", "cost 1", {"slippage_ticks_each_side": 1.0}),
        VariationSpec("cost_2", "cost 2", {"slippage_ticks_each_side": 2.0}),
        VariationSpec("ema", "ema", {"ema_fast": 8}),
    )
    groups = group_variations_by_detection(base, variations)
    assert sorted(len(group) for group in groups.values()) == [1, 2]
    cost_1 = apply_variation(base, variations[0])
    cost_2 = apply_variation(base, variations[1])
    assert detection_signature(cost_1) == detection_signature(cost_2)


def test_batch_contract_rejects_holdout_access(tmp_path) -> None:
    path = _write(
        tmp_path / "bad.yaml",
        """
study_id: BAD
status: DISCOVERY_ONLY
source_partition: recent_holdout
promotion_authorized: false
holdout_access_authorized: true
variations:
  - id: baseline
    overrides: {}
""".strip()
        + "\n",
    )
    with pytest.raises(ValueError, match="holdout"):
        load_batch_design(path, allowed_partitions={"primary_forward"})


def test_batch_contract_rejects_unknown_override(tmp_path) -> None:
    path = _write(
        tmp_path / "bad-field.yaml",
        """
study_id: BAD-FIELD
status: DISCOVERY_ONLY
source_partition: primary_forward
promotion_authorized: false
holdout_access_authorized: false
variations:
  - id: bad
    overrides:
      imaginary_parameter: 42
""".strip()
        + "\n",
    )
    with pytest.raises(ValueError, match="unsupported overrides"):
        load_batch_design(path, allowed_partitions={"primary_forward"})
