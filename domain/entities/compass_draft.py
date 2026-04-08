from pydantic import BaseModel


class CompassDraft(BaseModel):
    quick_commands: str = ""
    key_files: list[str] = []
    non_obvious_patterns: str = ""
    gotchas: str = ""
    see_also: list[str] = []
