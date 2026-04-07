from abc import ABC, abstractmethod

from domain.compass import ContextCompass


class CodeRepository(ABC):
    @abstractmethod
    def get_module_files(self, module_path: str) -> dict[str, str]:
        """Reads the codebase and returns {filename: content}"""
        pass


class AIExtractionService(ABC):
    @abstractmethod
    def extract_knowledge(self, code_snippets: dict[str, str]) -> ContextCompass:
        """Takes raw code and forces the AI to return a valid ContextCompass"""
        pass


class ContextStorage(ABC):
    @abstractmethod
    def save(self, module_path: str, compass: ContextCompass) -> None:
        """Saves the final compass to .ai_context/"""
        pass
