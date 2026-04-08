from dataclasses import dataclass
from datetime import datetime

from application.interfaces.compass_repository import CompassRepositoryInterface
from application.interfaces.relevance_scorer import RelevanceScorerInterface
from domain.exceptions import UnroutableQueryError


@dataclass
class RoutedPrompt:
    query: str
    context_blocks: list[str]
    enriched_prompt: str


class RouteQueryUseCase:
    def __init__(
        self,
        repo: CompassRepositoryInterface,
        scorer: RelevanceScorerInterface,
        top_n: int = 5,
    ):
        self._repo = repo
        self._scorer = scorer
        self._top_n = top_n

    def execute(self, query: str) -> RoutedPrompt:
        all_compasses = self._repo.list_all()
        current_time = datetime.now()

        fresh = [c for c in all_compasses if not c.is_stale(current_time, 0)]

        if not fresh:
            raise UnroutableQueryError("No fresh context compasses available.")

        scored = self._scorer.score(query, fresh)
        scored.sort(key=lambda pair: pair[1], reverse=True)
        top = scored[: self._top_n]

        context_blocks = [c.non_obvious_patterns for c, _ in top]
        injected = "\n---\n".join(context_blocks)
        enriched = f"System Context:\n{injected}\n\nUser Query: {query}"

        return RoutedPrompt(
            query=query,
            context_blocks=context_blocks,
            enriched_prompt=enriched,
        )
