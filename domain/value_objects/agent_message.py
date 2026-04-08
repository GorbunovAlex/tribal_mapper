from enum import Enum

from pydantic import BaseModel


class AgentStage(str, Enum):
    EXPLORE = "EXPLORE"
    ANALYSE = "ANALYSE"
    WRITE = "WRITE"
    CRITIQUE = "CRITIQUE"


class AgentMessage(BaseModel):
    model_config = {"frozen": True}

    source_module: str
    stage: AgentStage
    content: str
    confidence_score: float = 0.0
