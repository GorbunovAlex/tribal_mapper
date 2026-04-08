from datetime import datetime

from pydantic import BaseModel


class CodeModule(BaseModel):
    file_path: str
    raw_content: str
    language: str = ""
    last_modified: datetime | None = None
