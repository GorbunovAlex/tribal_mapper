import json
import re
from pathlib import Path

from application.interfaces.compass_repository import CompassRepositoryInterface
from domain.entities.code_module import CodeModule
from domain.entities.context_compass import ContextCompass


class LocalFileCompassRepository(CompassRepositoryInterface):
    def __init__(self, root: str = ".", base_dir: str = ".ai_context") -> None:
        self._base = Path(root).resolve() / base_dir
        self._base.mkdir(parents=True, exist_ok=True)

    def _safe_name(self, module_path: str) -> str:
        return re.sub(r"[^\w\-.]", "_", module_path)

    def save(self, compass: ContextCompass, module: CodeModule) -> None:
        filename = self._safe_name(module.file_path) + ".json"
        path = self._base / filename
        path.write_text(compass.model_dump_json(indent=2), encoding="utf-8")

    def load(self, module_path: str) -> ContextCompass | None:
        filename = self._safe_name(module_path) + ".json"
        path = self._base / filename
        if not path.exists():
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        return ContextCompass.model_validate(data)

    def list_all(self) -> list[ContextCompass]:
        compasses: list[ContextCompass] = []
        for path in self._base.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                compasses.append(ContextCompass.model_validate(data))
            except (json.JSONDecodeError, ValueError):
                continue
        return compasses
