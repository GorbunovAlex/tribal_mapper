from abc import ABC, abstractmethod

from domain.entities.context_compass import ContextCompass


class RelevanceScorerInterface(ABC):
    @abstractmethod
    def score(self, query: str, compasses: list[ContextCompass]) -> list[tuple[ContextCompass, float]]: ...
