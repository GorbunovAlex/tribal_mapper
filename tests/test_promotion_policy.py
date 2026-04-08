import pytest
from pydantic import ValidationError

from domain.entities.compass_draft import CompassDraft
from domain.exceptions import ContextTooLargeError, IncompleteDraftError
from domain.policies.compass_promotion import CompassPromotionPolicy


class TestCompassPromotionPolicy:
    def test_happy_path(self):
        draft = CompassDraft(
            quick_commands="make build",
            key_files=["main.py", "config.py"],
            non_obvious_patterns="uses DI container",
            gotchas="env vars required",
            see_also=["docs/"],
        )
        compass = CompassPromotionPolicy.promote(draft)

        assert compass.quick_commands == "make build"
        assert compass.key_files == ["main.py", "config.py"]
        assert compass.non_obvious_patterns == "uses DI container"
        assert compass.gotchas == "env vars required"
        assert compass.see_also == ["docs/"]
        assert compass.token_count.value >= 0

    def test_missing_quick_commands_raises(self):
        draft = CompassDraft(key_files=["main.py"])
        with pytest.raises(IncompleteDraftError, match="quick commands"):
            CompassPromotionPolicy.promote(draft)

    def test_missing_key_files_raises(self):
        draft = CompassDraft(quick_commands="make build")
        with pytest.raises(IncompleteDraftError, match="key files"):
            CompassPromotionPolicy.promote(draft)

    def test_empty_quick_commands_raises(self):
        draft = CompassDraft(quick_commands="", key_files=["a.py"])
        with pytest.raises(IncompleteDraftError, match="quick commands"):
            CompassPromotionPolicy.promote(draft)

    def test_empty_key_files_raises(self):
        draft = CompassDraft(quick_commands="make build", key_files=[])
        with pytest.raises(IncompleteDraftError, match="key files"):
            CompassPromotionPolicy.promote(draft)

    def test_context_too_large_raises(self):
        draft = CompassDraft(
            quick_commands="x" * 5000,
            key_files=["a.py"],
            non_obvious_patterns="y" * 5000,
        )
        with pytest.raises(ContextTooLargeError, match="exceeds.*ceiling"):
            CompassPromotionPolicy.promote(draft, token_ceiling=100)

    def test_custom_token_ceiling(self):
        draft = CompassDraft(
            quick_commands="build",
            key_files=["a.py"],
        )
        compass = CompassPromotionPolicy.promote(draft, token_ceiling=5000)
        assert compass.token_count.ceiling == 5000

    def test_result_is_frozen(self):
        draft = CompassDraft(
            quick_commands="make build",
            key_files=["main.py"],
        )
        compass = CompassPromotionPolicy.promote(draft)
        with pytest.raises(ValidationError):
            compass.quick_commands = "new"

    def test_token_count_estimated_correctly(self):
        draft = CompassDraft(
            quick_commands="abcd",  # 4 chars
            key_files=["abcd"],  # 4 chars
            non_obvious_patterns="abcdabcd",  # 8 chars
        )
        # total = 16 chars, estimated = 16 // 4 = 4
        compass = CompassPromotionPolicy.promote(draft)
        assert compass.token_count.value == 4
