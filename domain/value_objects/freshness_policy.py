from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FreshnessPolicy:
    max_days_old: int = 7
    max_commits_old: int = 10

    def is_stale(
        self, last_update: datetime, current_date: datetime, commits_since: int
    ) -> bool:
        days_old = (current_date - last_update).days
        return days_old > self.max_days_old or commits_since > self.max_commits_old
