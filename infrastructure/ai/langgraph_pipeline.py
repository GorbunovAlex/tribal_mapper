from langgraph.graph import END, StateGraph

from application.builders.compass_draft_builder import CompassDraftBuilder
from application.interfaces.extraction_pipeline import ExtractionPipelineInterface
from domain.entities.code_module import CodeModule
from domain.entities.compass_draft import CompassDraft
from infrastructure.ai.agent_factory import AgentFactory
from infrastructure.ai.graph_state import PipelineState
from infrastructure.ai.nodes import (
    make_analyse_node,
    make_critique_node,
    make_explore_node,
    make_write_node,
)


class LangGraphExtractionPipeline(ExtractionPipelineInterface):
    def __init__(self, agent_factory: AgentFactory, max_retries: int = 2) -> None:
        self._max_retries = max_retries
        self._graph = self._build_graph(agent_factory)

    def _build_graph(self, factory: AgentFactory):
        graph = StateGraph(PipelineState)

        # 1. Add nodes
        graph.add_node("explore", make_explore_node(factory.create_explorer()))
        graph.add_node("analyse", make_analyse_node(factory.create_analyst()))
        graph.add_node("write", make_write_node(factory.create_writer()))
        graph.add_node("critique", make_critique_node(factory.create_critic()))

        # 2. Linear edges: START → explore → analyse → write → critique
        graph.set_entry_point("explore")
        graph.add_edge("explore", "analyse")
        graph.add_edge("analyse", "write")
        graph.add_edge("write", "critique")

        # 3. Conditional edge: critique → done OR retry write
        def should_retry(state: PipelineState) -> str:
            score = state["critique"].confidence_score
            retries = state.get("retries", 0)
            if score >= 0.8 or retries >= self._max_retries:
                return "done"
            return "retry"

        graph.add_conditional_edges(
            "critique",
            should_retry,
            {"done": END, "retry": "write"},
        )

        return graph.compile()

    def run(self, module: CodeModule) -> CompassDraft:
        # Seed the initial state
        initial_state: PipelineState = {
            "source_module": module.file_path,
            "raw_content": module.raw_content,
            "explored": None,
            "analysed": None,
            "written": None,
            "critique": None,
            "retries": 0,
        }

        # Execute the graph — LangGraph runs nodes in order,
        # following edges until it hits END
        final_state = self._graph.invoke(initial_state)

        # Assemble the draft from final state
        builder = CompassDraftBuilder()
        builder.add_quick_commands(final_state["written"].content)
        builder.add_key_files([module.file_path])
        builder.add_patterns(final_state["critique"].content)
        return builder.build()
