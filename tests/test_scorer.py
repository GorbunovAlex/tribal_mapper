from unittest.mock import MagicMock, patch

from domain.entities.compass_draft import CompassDraft
from domain.entities.context_compass import ContextCompass
from domain.policies.compass_promotion import CompassPromotionPolicy
from infrastructure.ai.embedding_scorer import (
    EmbeddingRelevanceScorer,
    _compass_text,
    _cosine_similarity,
)


def _make_compass(commands: str, patterns: str) -> ContextCompass:
    draft = CompassDraft(
        quick_commands=commands,
        key_files=["main.py"],
        non_obvious_patterns=patterns,
    )
    return CompassPromotionPolicy.promote(draft)


class TestCosineHelper:
    def test_identical_vectors(self):
        assert _cosine_similarity([1, 0, 0], [1, 0, 0]) == 1.0

    def test_orthogonal_vectors(self):
        assert abs(_cosine_similarity([1, 0], [0, 1])) < 1e-9

    def test_zero_vector(self):
        assert _cosine_similarity([0, 0], [1, 1]) == 0.0


class TestCompassText:
    def test_combines_fields(self):
        compass = _make_compass("build", "singleton pattern")
        text = _compass_text(compass)
        assert "build" in text
        assert "singleton pattern" in text
        assert "main.py" in text


class TestEmbeddingRelevanceScorer:
    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    def test_scores_relevant_higher(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_embeddings_cls.return_value = mock_instance
        # query=token refresh, auth compass=similar, db compass=orthogonal
        mock_instance.embed_documents.return_value = [
            [1.0, 0.0, 0.0],  # query: "token refresh"
            [0.9, 0.1, 0.0],  # auth compass: similar
            [0.0, 0.0, 1.0],  # db compass: different
        ]

        scorer = EmbeddingRelevanceScorer(model="text-embedding-3-small")
        auth_compass = _make_compass("login", "JWT token refresh flow")
        db_compass = _make_compass("migrate", "database connection pooling")

        results = scorer.score("token refresh", [auth_compass, db_compass])

        scores = {c.quick_commands: s for c, s in results}
        assert scores["login"] > scores["migrate"]

    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    def test_empty_query_returns_zero_scores(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_embeddings_cls.return_value = mock_instance

        scorer = EmbeddingRelevanceScorer()
        compass = _make_compass("build", "pattern")

        results = scorer.score("", [compass])
        assert len(results) == 1
        assert results[0][1] == 0.0
        mock_instance.embed_documents.assert_not_called()

    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    def test_no_compasses(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_embeddings_cls.return_value = mock_instance

        scorer = EmbeddingRelevanceScorer()
        results = scorer.score("query", [])
        assert results == []
        mock_instance.embed_documents.assert_not_called()

    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    def test_multiple_compasses_all_scored(self, mock_embeddings_cls):
        mock_instance = MagicMock()
        mock_embeddings_cls.return_value = mock_instance
        mock_instance.embed_documents.return_value = [
            [1.0, 0.0],  # query
            [0.8, 0.2],  # compass 1
            [0.5, 0.5],  # compass 2
            [0.1, 0.9],  # compass 3
        ]

        scorer = EmbeddingRelevanceScorer()
        compasses = [
            _make_compass("a", "p1"),
            _make_compass("b", "p2"),
            _make_compass("c", "p3"),
        ]

        results = scorer.score("query", compasses)
        assert len(results) == 3
        scores = [s for _, s in results]
        # Scores should be descending (first compass most similar to query)
        assert scores[0] > scores[1] > scores[2]
