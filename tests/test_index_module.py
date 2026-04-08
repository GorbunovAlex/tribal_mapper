from unittest.mock import MagicMock

from application.use_cases.index_module import IndexModuleUseCase
from domain.entities.code_module import CodeModule
from domain.entities.compass_draft import CompassDraft


def _make_module(path: str = "src/auth.py", content: str = "pass") -> CodeModule:
    return CodeModule(file_path=path, raw_content=content)


class TestIndexModuleUseCase:
    def test_successful_indexing(self):
        draft = CompassDraft(
            quick_commands="make build",
            key_files=["main.py"],
            non_obvious_patterns="uses DI",
        )
        pipeline = MagicMock()
        pipeline.run.return_value = draft
        repo = MagicMock()

        use_case = IndexModuleUseCase(pipeline, repo)
        result = use_case.execute(_make_module())

        assert result is True
        pipeline.run.assert_called_once()
        repo.save.assert_called_once()

    def test_incomplete_draft_skips(self):
        draft = CompassDraft()  # empty — missing required fields
        pipeline = MagicMock()
        pipeline.run.return_value = draft
        repo = MagicMock()

        use_case = IndexModuleUseCase(pipeline, repo)
        result = use_case.execute(_make_module())

        assert result is False
        repo.save.assert_not_called()

    def test_context_too_large_skips(self):
        draft = CompassDraft(
            quick_commands="x" * 5000,
            key_files=["a.py"],
            non_obvious_patterns="y" * 5000,
        )
        pipeline = MagicMock()
        pipeline.run.return_value = draft
        repo = MagicMock()

        use_case = IndexModuleUseCase(pipeline, repo, token_ceiling=10)
        result = use_case.execute(_make_module())

        assert result is False
        repo.save.assert_not_called()

    def test_token_ceiling_passed_through(self):
        draft = CompassDraft(
            quick_commands="build",
            key_files=["a.py"],
        )
        pipeline = MagicMock()
        pipeline.run.return_value = draft
        repo = MagicMock()

        use_case = IndexModuleUseCase(pipeline, repo, token_ceiling=5000)
        result = use_case.execute(_make_module())

        assert result is True
        saved_compass = repo.save.call_args[0][0]
        assert saved_compass.token_count.ceiling == 5000
