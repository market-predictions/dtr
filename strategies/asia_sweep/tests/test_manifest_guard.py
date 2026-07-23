from __future__ import annotations

from dtr_lab.strategies.asia_sweep.manifest_guard import event_runner_block_reason


def test_manifest_without_block_reason_is_runnable() -> None:
    assert event_runner_block_reason({"qualification_status": "REGISTERED"}) is None


def test_manifest_block_reason_is_normalized() -> None:
    dataset = {
        "event_runner_blocked_reason": "  proxy_timezone_activity_adapter_not_implemented  "
    }
    assert (
        event_runner_block_reason(dataset)
        == "proxy_timezone_activity_adapter_not_implemented"
    )


def test_blank_manifest_block_reason_is_ignored() -> None:
    assert event_runner_block_reason({"event_runner_blocked_reason": "   "}) is None
