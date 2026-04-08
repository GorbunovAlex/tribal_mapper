from domain.entities.code_module import CodeModule
from domain.entities.compass_draft import CompassDraft
from domain.policies.compass_promotion import CompassPromotionPolicy
from infrastructure.storage.local_fs_repository import LocalFileCompassRepository


def _make_compass():
    draft = CompassDraft(
        quick_commands="make build",
        key_files=["main.py"],
        non_obvious_patterns="uses DI",
    )
    return CompassPromotionPolicy.promote(draft)


def _make_module(path: str = "src/auth.py") -> CodeModule:
    return CodeModule(file_path=path, raw_content="pass")


class TestLocalFileCompassRepository:
    def test_save_creates_file(self, tmp_path):
        repo = LocalFileCompassRepository(base_dir=str(tmp_path / ".ai_context"))
        compass = _make_compass()
        module = _make_module()

        repo.save(compass, module)

        files = list((tmp_path / ".ai_context").glob("*.json"))
        assert len(files) == 1

    def test_load_returns_saved_compass(self, tmp_path):
        repo = LocalFileCompassRepository(base_dir=str(tmp_path / ".ai_context"))
        compass = _make_compass()
        module = _make_module("src/auth.py")

        repo.save(compass, module)
        loaded = repo.load("src/auth.py")

        assert loaded is not None
        assert loaded.quick_commands == compass.quick_commands
        assert loaded.key_files == compass.key_files

    def test_load_nonexistent_returns_none(self, tmp_path):
        repo = LocalFileCompassRepository(base_dir=str(tmp_path / ".ai_context"))
        assert repo.load("nonexistent.py") is None

    def test_list_all(self, tmp_path):
        repo = LocalFileCompassRepository(base_dir=str(tmp_path / ".ai_context"))

        repo.save(_make_compass(), _make_module("a.py"))
        repo.save(_make_compass(), _make_module("b.py"))

        all_compasses = repo.list_all()
        assert len(all_compasses) == 2

    def test_list_all_skips_invalid_json(self, tmp_path):
        base = tmp_path / ".ai_context"
        base.mkdir()
        (base / "bad.json").write_text("not valid json", encoding="utf-8")

        repo = LocalFileCompassRepository(base_dir=str(base))
        assert repo.list_all() == []

    def test_safe_name_sanitises_paths(self, tmp_path):
        repo = LocalFileCompassRepository(base_dir=str(tmp_path / ".ai_context"))
        compass = _make_compass()
        module = _make_module("src/nested/deep/file.py")

        repo.save(compass, module)
        loaded = repo.load("src/nested/deep/file.py")
        assert loaded is not None
