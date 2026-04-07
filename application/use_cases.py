from application.interfaces import AIExtractionService, CodeRepository, ContextStorage
from domain.compass import ContextCompass


class MapTribalKnowledgeUseCase:
    """Controller. Orchestrates the flow."""

    def __init__(
        self,
        code_repository: CodeRepository,
        ai_extraction_service: AIExtractionService,
        storage: ContextStorage,
    ):
        self.code_repository = code_repository
        self.ai_extraction_service = ai_extraction_service
        self.storage = storage

    def execute(self, module_path: str) -> ContextCompass:
        files = self.code_repository.get_module_files(module_path)
        compass = self.ai_extraction_service.extract_knowledge(files)
        self.storage.save(module_path, compass)
        return compass
