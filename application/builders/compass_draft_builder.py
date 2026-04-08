from domain.entities.compass_draft import CompassDraft


class CompassDraftBuilder:
    def __init__(self) -> None:
        self._quick_commands: str = ""
        self._key_files: list[str] = []
        self._non_obvious_patterns: str = ""
        self._gotchas: str = ""
        self._see_also: list[str] = []

    def add_quick_commands(self, content: str) -> "CompassDraftBuilder":
        self._quick_commands = content
        return self

    def add_key_files(self, files: list[str]) -> "CompassDraftBuilder":
        self._key_files = files
        return self

    def add_patterns(self, content: str) -> "CompassDraftBuilder":
        self._non_obvious_patterns = content
        return self

    def add_gotchas(self, content: str) -> "CompassDraftBuilder":
        self._gotchas = content
        return self

    def add_see_also(self, links: list[str]) -> "CompassDraftBuilder":
        self._see_also = links
        return self

    def build(self) -> CompassDraft:
        return CompassDraft(
            quick_commands=self._quick_commands,
            key_files=self._key_files,
            non_obvious_patterns=self._non_obvious_patterns,
            gotchas=self._gotchas,
            see_also=self._see_also,
        )
