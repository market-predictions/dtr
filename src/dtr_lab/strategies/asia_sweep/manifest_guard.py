from __future__ import annotations

from collections.abc import Mapping


def event_runner_block_reason(dataset: Mapping[str, object]) -> str | None:
    """Return a manifest-declared event-runner block reason, if present."""

    value = dataset.get("event_runner_blocked_reason")
    if value is None:
        return None
    reason = str(value).strip()
    return reason or None
