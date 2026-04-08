from __future__ import annotations

from typing import TYPE_CHECKING

from config.interfaces import AgentsConfig
from domain.value_objects.agent_message import AgentStage
from infrastructure.ai.base import IAgent
from infrastructure.ai.llm_agent import LLMAgent

if TYPE_CHECKING:
    from infrastructure.ai.rate_limiter import RateLimiter


class AgentFactory:
    def __init__(
        self,
        config: AgentsConfig,
        api_key: str = "",
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._config = config
        self._api_key = api_key
        self._rate_limiter = rate_limiter

    def create_explorer(self) -> IAgent:
        return LLMAgent(
            self._config.explorer, AgentStage.EXPLORE, self._api_key, self._rate_limiter
        )

    def create_analyst(self) -> IAgent:
        return LLMAgent(
            self._config.analyst, AgentStage.ANALYSE, self._api_key, self._rate_limiter
        )

    def create_writer(self) -> IAgent:
        return LLMAgent(
            self._config.writer, AgentStage.WRITE, self._api_key, self._rate_limiter
        )

    def create_critic(self) -> IAgent:
        return LLMAgent(
            self._config.critic, AgentStage.CRITIQUE, self._api_key, self._rate_limiter
        )
