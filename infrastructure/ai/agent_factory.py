from config.interfaces import AgentsConfig
from domain.value_objects.agent_message import AgentStage
from infrastructure.ai.base import IAgent
from infrastructure.ai.llm_agent import LLMAgent


class AgentFactory:
    def __init__(self, config: AgentsConfig) -> None:
        self._config = config

    def create_explorer(self) -> IAgent:
        return LLMAgent(self._config.explorer, AgentStage.EXPLORE)

    def create_analyst(self) -> IAgent:
        return LLMAgent(self._config.analyst, AgentStage.ANALYSE)

    def create_writer(self) -> IAgent:
        return LLMAgent(self._config.writer, AgentStage.WRITE)

    def create_critic(self) -> IAgent:
        return LLMAgent(self._config.critic, AgentStage.CRITIQUE)
