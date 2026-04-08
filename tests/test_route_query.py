from unittest.mock import MagicMock

import pytest

from application.use_cases.route_query import RoutedPrompt, RouteQueryUseCase
from domain.entities.compass_draft import CompassDraft
from domain.entities.context_compass import ContextCompass
from domain.exceptions import UnroutableQueryError
from domain.policies.compass_promotion import CompassPromotionPolicy


def _make_compass(
    commands: str = "make build",
    patterns: str = "uses DI",
) -> ContextCompass:
    draft = CompassDraft(
        quick_commands=commands,
        key_files=["main.py"],
        non_obvious_patterns=patterns,
    )
    return CompassPromotionPolicy.promote(draft)


class TestRouteQueryUseCase:
    def test_returns_routed_prompt(self):
        compass = _make_compass()
        repo = MagicMock()
        repo.list_all.return_value = [compass]
        scorer = MagicMock()
        scorer.score.return_value = [(compass, 0.9)]

        use_case = RouteQueryUseCase(repo, scorer)
        result = use_case.execute("how does auth work?")

        assert isinstance(result, RoutedPrompt)
        assert result.query == "how does auth work?"
        assert len(result.context_blocks) == 1
        assert "uses DI" in result.enriched_prompt

    def test_raises_when_no_fresh_compasses(self):
        repo = MagicMock()
        repo.list_all.return_value = []
        scorer = MagicMock()

        use_case = RouteQueryUseCase(repo, scorer)
        with pytest.raises(UnroutableQueryError, match="No fresh"):
            use_case.execute("any query")

    def test_top_n_limits_results(self):
        compasses = [_make_compass(patterns=f"pattern {i}") for i in range(10)]
        repo = MagicMock()
        repo.list_all.return_value = compasses
        scorer = MagicMock()
        scorer.score.return_value = [
            (c, 1.0 - i * 0.1) for i, c in enumerate(compasses)
        ]

        use_case = RouteQueryUseCase(repo, scorer, top_n=3)
        result = use_case.execute("query")

        assert len(result.context_blocks) == 3

    def test_scorer_is_called_with_fresh_compasses(self):
        compass = _make_compass()
        repo = MagicMock()
        repo.list_all.return_value = [compass]
        scorer = MagicMock()
        scorer.score.return_value = [(compass, 0.5)]

        use_case = RouteQueryUseCase(repo, scorer)
        use_case.execute("query")

        scorer.score.assert_called_once()
        query_arg, compasses_arg = scorer.score.call_args[0]
        assert query_arg == "query"
        assert len(compasses_arg) == 1
