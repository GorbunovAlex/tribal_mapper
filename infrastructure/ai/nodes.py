from domain.value_objects.agent_message import AgentMessage, AgentStage
from infrastructure.ai.base import IAgent
from infrastructure.ai.graph_state import PipelineState


def make_explore_node(agent: IAgent):
    def explore(state: PipelineState) -> dict:
        seed = AgentMessage(
            source_module=state["source_module"],
            stage=AgentStage.EXPLORE,
            content=state["raw_content"],
        )
        return {"explored": agent.invoke(seed)}

    return explore


def make_analyse_node(agent: IAgent):
    def analyse(state: PipelineState) -> dict:
        return {"analysed": agent.invoke(state["explored"])}

    return analyse


def make_write_node(agent: IAgent):
    def write(state: PipelineState) -> dict:
        # On first pass, input is analysed; on retry, input is critique
        input_msg = state["critique"] if state.get("critique") else state["analysed"]
        return {"written": agent.invoke(input_msg)}

    return write


def make_critique_node(agent: IAgent):
    def critique(state: PipelineState) -> dict:
        result = agent.invoke(state["written"])
        return {
            "critique": result,
            "retries": state.get("retries", 0) + 1,
        }

    return critique
