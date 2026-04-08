from __future__ import annotations

from typing import TYPE_CHECKING

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config.interfaces import AgentConfig
from domain.value_objects.agent_message import AgentMessage, AgentStage
from infrastructure.ai.base import IAgent

if TYPE_CHECKING:
    from infrastructure.ai.rate_limiter import RateLimiter


class LLMAgent(IAgent):
    def __init__(
        self,
        config: AgentConfig,
        stage: AgentStage,
        api_key: str = "",
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self._stage = stage
        self._system_prompt = config.system_prompt
        self._rate_limiter = rate_limiter
        self._llm = ChatOpenAI(
            model=config.model,
            temperature=config.temperature,
            api_key=api_key or None,
        )

    def _parse_confidence(self, content: str) -> float:
        """Extract confidence if the critic embeds one, else default to 1.0."""
        import re

        match = re.search(r"confidence[:\s]+([0-9]*\.?[0-9]+)", content, re.IGNORECASE)
        return float(match.group(1)) if match else 1.0

    def invoke(self, message: AgentMessage) -> AgentMessage:
        if self._rate_limiter:
            self._rate_limiter.acquire()
        response = self._llm.invoke(
            [
                SystemMessage(content=self._system_prompt),
                HumanMessage(content=message.content),
            ]
        )
        return AgentMessage(
            source_module=message.source_module,
            stage=self._stage,
            content=response.content,
            confidence_score=self._parse_confidence(response.content),
        )
