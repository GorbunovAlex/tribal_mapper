from datetime import datetime

from pydantic import BaseModel, Field

from domain.value_objects.freshness_policy import FreshnessPolicy
from domain.value_objects.token_count import TokenCount


class ContextCompass(BaseModel):
    model_config = {"frozen": True}

    quick_commands: str
    key_files: list[str]
    non_obvious_patterns: str
    gotchas: str = ""
    see_also: list[str] = []
    token_count: TokenCount
    last_updated: datetime
    policy: FreshnessPolicy = Field(default_factory=FreshnessPolicy)

    def is_stale(self, current_date: datetime, commit_count: int) -> bool:
        return self.policy.is_stale(self.last_updated, current_date, commit_count)
