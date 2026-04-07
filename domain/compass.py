from typing import List
from pydantic import BaseModel, Field, model_validator


class ContextCompass(BaseModel):
    quick_commands: str = Field(
        ..., description="Copy-paste operations and frequent CLI commands."
    )
    key_files: List[str] = Field(
        ..., max_length=5, description="Strictly limited to 3-5 critical files."
    )
    non_obvious_patterns: str = Field(
        ..., min_length=20, description="The core tribal knowledge and hidden rules."
    )
    see_also: List[str] = Field(
        default_factory=list, description="Cross-references to related modules."
    )

    @model_validator(mode="after")
    def validate_total_size(self) -> "ContextCompass":
        total_size = len(self.quick_commands) + len(self.non_obvious_patterns)
        if total_size > 2500:
            raise ValueError("Compass exceeded maximum size. AI must be more concise.")
        return self
