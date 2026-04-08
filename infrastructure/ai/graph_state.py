from typing import TypedDict

from domain.value_objects.agent_message import AgentMessage


class PipelineState(TypedDict):
    source_module: str
    raw_content: str
    explored: AgentMessage | None
    analysed: AgentMessage | None
    written: AgentMessage | None
    critique: AgentMessage | None
    retries: int
