import logging

from application.interfaces.compass_repository import CompassRepositoryInterface
from application.interfaces.extraction_pipeline import ExtractionPipelineInterface
from domain.entities.code_module import CodeModule
from domain.exceptions import DomainError
from domain.policies.compass_promotion import CompassPromotionPolicy

logger = logging.getLogger(__name__)


class IndexModuleUseCase:
    def __init__(
        self,
        pipeline: ExtractionPipelineInterface,
        repo: CompassRepositoryInterface,
        token_ceiling: int = 1000,
    ):
        self._pipeline = pipeline
        self._repo = repo
        self._token_ceiling = token_ceiling

    def execute(self, module: CodeModule) -> bool:
        try:
            draft = self._pipeline.run(module)
            compass = CompassPromotionPolicy.promote(
                draft, token_ceiling=self._token_ceiling
            )
            self._repo.save(compass, module)
            return True
        except DomainError as e:
            logger.warning("Skipped %s: %s", module.file_path, e)
            return False
