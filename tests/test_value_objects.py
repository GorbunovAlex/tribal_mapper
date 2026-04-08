from datetime import datetime, timedelta

import pytest
from pydantic import ValidationError

from domain.exceptions import ContextTooLargeError
from domain.value_objects.agent_message import AgentMessage, AgentStage
from domain.value_objects.freshness_policy import FreshnessPolicy
from domain.value_objects.token_count import TokenCount


class TestTokenCount:
    def test_valid_token_count(self):
        tc = TokenCount(value=500, ceiling=1000)
        assert tc.value == 500
        assert tc.ceiling == 1000

    def test_at_ceiling_is_valid(self):
        tc = TokenCount(value=1000, ceiling=1000)
        assert tc.value == 1000

    def test_exceeds_ceiling_raises(self):
        with pytest.raises(ContextTooLargeError, match="2000.*1000"):
            TokenCount(value=2000, ceiling=1000)

    def test_default_ceiling(self):
        tc = TokenCount(value=100)
        assert tc.ceiling == 1000

    def test_frozen(self):
        tc = TokenCount(value=100)
        with pytest.raises(AttributeError):
            tc.value = 200


class TestFreshnessPolicy:
    def test_fresh_compass(self):
        policy = FreshnessPolicy(max_days_old=7, max_commits_old=10)
        now = datetime.now()
        last_update = now - timedelta(days=3)
        assert policy.is_stale(last_update, now, commits_since=5) is False

    def test_stale_by_days(self):
        policy = FreshnessPolicy(max_days_old=7, max_commits_old=10)
        now = datetime.now()
        last_update = now - timedelta(days=10)
        assert policy.is_stale(last_update, now, commits_since=0) is True

    def test_stale_by_commits(self):
        policy = FreshnessPolicy(max_days_old=7, max_commits_old=10)
        now = datetime.now()
        last_update = now - timedelta(days=1)
        assert policy.is_stale(last_update, now, commits_since=15) is True

    def test_exactly_at_threshold_not_stale(self):
        policy = FreshnessPolicy(max_days_old=7, max_commits_old=10)
        now = datetime.now()
        last_update = now - timedelta(days=7)
        assert policy.is_stale(last_update, now, commits_since=10) is False

    def test_custom_thresholds(self):
        policy = FreshnessPolicy(max_days_old=30, max_commits_old=50)
        now = datetime.now()
        last_update = now - timedelta(days=20)
        assert policy.is_stale(last_update, now, commits_since=40) is False


class TestAgentMessage:
    def test_creation(self):
        msg = AgentMessage(
            source_module="src/auth.py",
            stage=AgentStage.EXPLORE,
            content="module content",
        )
        assert msg.source_module == "src/auth.py"
        assert msg.stage == AgentStage.EXPLORE
        assert msg.confidence_score == 0.0

    def test_frozen(self):
        msg = AgentMessage(
            source_module="src/auth.py",
            stage=AgentStage.EXPLORE,
            content="content",
        )
        with pytest.raises(ValidationError):
            msg.content = "new content"

    def test_all_stages_exist(self):
        stages = {s.value for s in AgentStage}
        assert stages == {"EXPLORE", "ANALYSE", "WRITE", "CRITIQUE"}
