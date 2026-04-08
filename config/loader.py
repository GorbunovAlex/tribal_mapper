# config/loader.py
from pathlib import Path

import yaml

from config.interfaces import AppConfig

_CONFIG_DIR = Path(__file__).resolve().parent
_singleton: AppConfig | None = None


def load_config(path: str | Path | None = None) -> AppConfig:
    global _singleton
    if _singleton is not None:
        return _singleton

    if path is None:
        path = _CONFIG_DIR / "mapper.yaml"
    else:
        path = Path(path)

    raw: dict = {}
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

    _singleton = AppConfig.model_validate(raw)
    return _singleton


def reset_config() -> None:
    """Reset the singleton — mainly useful for tests."""
    global _singleton
    _singleton = None
