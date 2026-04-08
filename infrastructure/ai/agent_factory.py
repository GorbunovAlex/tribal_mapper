from abc import ABC, abstractmethod

from config.interfaces import AgentsConfig
from domain.value_objects.agent_message import AgentMessage


class IAgent(ABC):
    @abstractmethod
    def invoke(self, message: AgentMessage) -> AgentMessage: ...


class AgentFactory:
    def __init__(self, config: AgentsConfig) -> None:
        self._config = config

    def create_explorer(self) -> IAgent:
        raise NotImplementedError("LangGraph agent not yet wired")

    def create_analyst(self) -> IAgent:
        raise NotImplementedError("LangGraph agent not yet wired")

    def create_writer(self) -> IAgent:
        raise NotImplementedError("LangGraph agent not yet wired")

    def create_critic(self) -> IAgent:
        raise NotImplementedError("LangGraph agent not yet wired")
