from __future__ import annotations

import run_wayne_staged_sequence_pair as runner

from dtr_lab.strategies.wayne_direction import data

INDEPENDENT_REPLICATION_PAIRS = ("EURGBP", "EURJPY", "GBPJPY", "NZDUSD")

# Keep the development runner and loader unchanged. This research-only wrapper
# admits only the panel frozen before outcomes in v0.9.
data.PRIMARY_PAIRS = tuple(
    sorted(set(data.PRIMARY_PAIRS + INDEPENDENT_REPLICATION_PAIRS))
)
runner.PRIMARY_PAIRS = INDEPENDENT_REPLICATION_PAIRS


if __name__ == "__main__":
    runner.main()
