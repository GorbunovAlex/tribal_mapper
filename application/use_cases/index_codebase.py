import asyncio
import logging
from dataclasses import dataclass, field

from application.interfaces.code_repository import CodeRepositoryInterface
from application.use_cases.index_module import IndexModuleUseCase

logger = logging.getLogger(__name__)


@dataclass
class IndexingReport:
    succeeded: int = 0
    skipped: int = 0
    failed: int = 0
    errors: list[str] = field(default_factory=list)


class IndexCodebaseUseCase:
    def __init__(
        self,
        code_repo: CodeRepositoryInterface,
        index_module: IndexModuleUseCase,
    ):
        self._code_repo = code_repo
        self._index_module = index_module

    async def execute(self, root: str) -> IndexingReport:
        modules = self._code_repo.list_modules(root)
        report = IndexingReport()

        async def _index_one(module):
            try:
                ok = self._index_module.execute(module)
                if ok:
                    report.succeeded += 1
                else:
                    report.skipped += 1
            except Exception as e:
                report.failed += 1
                report.errors.append(f"{module.file_path}: {e}")
                logger.error("Failed to index %s: %s", module.file_path, e)

        await asyncio.gather(*[_index_one(m) for m in modules])
        return report
