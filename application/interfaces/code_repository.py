from abc import ABC, abstractmethod
from datetime import datetime

from domain.entities.code_module import CodeModule


class CodeRepositoryInterface(ABC):
    @abstractmethod
    def list_modules(self, root: str) -> list[CodeModule]: ...

    @abstractmethod
    def get_commit_count_since(self, module: CodeModule, since: datetime) -> int: ...
