from config.interfaces import AgentsConfig
from domain.value_objects.agent_message import AgentStage
from infrastructure.ai.base import IAgent
from infrastructure.ai.llm_agent import LLMAgent


class AgentFactory:
    def __init__(self, config: AgentsConfig, api_key: str = "") -> None:
        self._config = config
        self._api_key = api_key

    def create_explorer(self) -> IAgent:
        return LLMAgent(self._config.explorer, AgentStage.EXPLORE, self._api_key)

    def create_analyst(self) -> IAgent:
        return LLMAgent(self._config.analyst, AgentStage.ANALYSE, self._api_key)

    def create_writer(self) -> IAgent:
        return LLMAgent(self._config.writer, AgentStage.WRITE, self._api_key)

    def create_critic(self) -> IAgent:
        return LLMAgent(self._config.critic, AgentStage.CRITIQUE, self._api_key)
