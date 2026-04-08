from application.builders.compass_draft_builder import CompassDraftBuilder
from domain.entities.compass_draft import CompassDraft


class TestCompassDraftBuilder:
    def test_build_empty(self):
        draft = CompassDraftBuilder().build()
        assert draft.quick_commands == ""
        assert draft.key_files == []
        assert draft.non_obvious_patterns == ""
        assert draft.gotchas == ""
        assert draft.see_also == []

    def test_build_full(self):
        draft = (
            CompassDraftBuilder()
            .add_quick_commands("make test")
            .add_key_files(["a.py", "b.py"])
            .add_patterns("singleton pattern")
            .add_gotchas("needs env var")
            .add_see_also(["docs/", "README.md"])
            .build()
        )
        assert draft.quick_commands == "make test"
        assert draft.key_files == ["a.py", "b.py"]
        assert draft.non_obvious_patterns == "singleton pattern"
        assert draft.gotchas == "needs env var"
        assert draft.see_also == ["docs/", "README.md"]

    def test_build_returns_compass_draft(self):
        draft = CompassDraftBuilder().build()
        assert isinstance(draft, CompassDraft)

    def test_builder_never_raises(self):
        # Builder should never validate — that's the policy's job
        draft = CompassDraftBuilder().build()
        assert draft.quick_commands == ""
        assert draft.key_files == []
