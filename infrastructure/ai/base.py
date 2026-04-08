from abc import ABC, abstractmethod

from domain.value_objects.agent_message import AgentMessage


class IAgent(ABC):
    @abstractmethod
    def invoke(self, message: AgentMessage) -> AgentMessage: ...
