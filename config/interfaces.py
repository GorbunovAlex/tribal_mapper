import os

from pydantic import BaseModel, Field


class FreshnessConfig(BaseModel):
    max_days_old: int = 7
    max_commits_old: int = 10


class AgentConfig(BaseModel):
    model: str = "gpt-4o"
    temperature: float = 0.3
    system_prompt: str = ""


class AgentsConfig(BaseModel):
    explorer: AgentConfig = AgentConfig(temperature=0.2)
    analyst: AgentConfig = AgentConfig(temperature=0.3)
    writer: AgentConfig = AgentConfig(temperature=0.4)
    critic: AgentConfig = AgentConfig(temperature=0.1)


class AppConfig(BaseModel):
    model_config = {"frozen": True}

    openai_api_key: str = Field(
        default_factory=lambda: os.environ.get("OPENAI_API_KEY", "")
    )
    freshness: FreshnessConfig = FreshnessConfig()
    token_ceiling: int = 1000
    extensions: list[str] = [".py", ".js", ".ts"]
    agents: AgentsConfig = AgentsConfig()
    embedding_model: str = "text-embedding-3-small"
