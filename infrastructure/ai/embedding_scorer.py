from application.interfaces.relevance_scorer import RelevanceScorerInterface
from domain.entities.context_compass import ContextCompass


class EmbeddingRelevanceScorer(RelevanceScorerInterface):
    def score(
        self, query: str, compasses: list[ContextCompass]
    ) -> list[tuple[ContextCompass, float]]:
        results: list[tuple[ContextCompass, float]] = []
        query_lower = query.lower()
        for compass in compasses:
            text = (
                compass.quick_commands + " " + compass.non_obvious_patterns
            ).lower()
            overlap = sum(1 for word in query_lower.split() if word in text)
            score = overlap / max(len(query_lower.split()), 1)
            results.append((compass, score))
        return results
