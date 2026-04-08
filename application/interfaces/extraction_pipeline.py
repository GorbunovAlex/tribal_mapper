from abc import ABC, abstractmethod

from domain.entities.code_module import CodeModule
from domain.entities.compass_draft import CompassDraft


class ExtractionPipelineInterface(ABC):
    @abstractmethod
    def run(self, module: CodeModule) -> CompassDraft: ...
