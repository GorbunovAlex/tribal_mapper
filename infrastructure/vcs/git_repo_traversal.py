import os
import subprocess
from datetime import datetime
from pathlib import Path

from application.interfaces.code_repository import CodeRepositoryInterface
from domain.entities.code_module import CodeModule

DEFAULT_EXTENSIONS = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java"}

DEFAULT_IGNORE_PATTERNS = [
    "node_modules/",
    "__pycache__/",
    ".venv/",
    "venv/",
    ".env/",
    "dist/",
    "build/",
    ".git/",
    ".tox/",
    ".mypy_cache/",
    ".pytest_cache/",
    ".ruff_cache/",
    "egg-info/",
    ".ai_context/",
]


class GitRepoTraversal(CodeRepositoryInterface):
    def __init__(self, extensions: set[str] | None = None) -> None:
        self._extensions = extensions or DEFAULT_EXTENSIONS

    def list_modules(self, root: str) -> list[CodeModule]:
        root_path = Path(root).resolve()
        ignore_path = root_path / ".mapperignore"
        ignored_patterns = self._load_ignore(ignore_path)

        modules: list[CodeModule] = []
        for dirpath, _dirnames, filenames in os.walk(root_path):
            rel_dir = Path(dirpath).relative_to(root_path)
            if any(part.startswith(".") for part in rel_dir.parts):
                continue
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix not in self._extensions:
                    continue
                rel = str(fpath.relative_to(root_path))
                if any(pat in rel for pat in ignored_patterns):
                    continue
                try:
                    content = fpath.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    continue
                stat = fpath.stat()
                modules.append(
                    CodeModule(
                        file_path=rel,
                        raw_content=content,
                        language=fpath.suffix.lstrip("."),
                        last_modified=datetime.fromtimestamp(stat.st_mtime),
                    )
                )
        return modules

    def get_commit_count_since(self, module: CodeModule, since: datetime) -> int:
        since_str = since.strftime("%Y-%m-%dT%H:%M:%S")
        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    "--oneline",
                    f"--since={since_str}",
                    "--",
                    module.file_path,
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            return (
                len(result.stdout.strip().splitlines()) if result.stdout.strip() else 0
            )
        except FileNotFoundError:
            return 0

    @staticmethod
    def _load_ignore(path: Path) -> list[str]:
        patterns = list(DEFAULT_IGNORE_PATTERNS)
        if path.exists():
            lines = path.read_text(encoding="utf-8").splitlines()
            patterns.extend(
                line.strip()
                for line in lines
                if line.strip() and not line.startswith("#")
            )
        return patterns
