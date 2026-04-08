from abc import ABC, abstractmethod

from domain.entities.code_module import CodeModule
from domain.entities.context_compass import ContextCompass


class CompassRepositoryInterface(ABC):
    @abstractmethod
    def save(self, compass: ContextCompass, module: CodeModule) -> None: ...

    @abstractmethod
    def load(self, module_path: str) -> ContextCompass | None: ...

    @abstractmethod
    def list_all(self) -> list[ContextCompass]: ...
