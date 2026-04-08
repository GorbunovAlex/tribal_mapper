import json
import logging

from langgraph.graph import END, StateGraph

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

logger = logging.getLogger(__name__)


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

    @staticmethod
    def _parse_writer_output(content: str, module_path: str) -> CompassDraft:
        """Parse structured JSON from the writer agent into a CompassDraft.

        Falls back to treating the raw content as quick_commands if
        JSON parsing fails, so the pipeline never crashes.
        """
        try:
            data = json.loads(content)
            return CompassDraft(
                quick_commands=data.get("quick_commands", ""),
                key_files=data.get("key_files", [module_path]),
                non_obvious_patterns=data.get("non_obvious_patterns", ""),
                gotchas=data.get("gotchas", ""),
                see_also=data.get("see_also", []),
            )
        except (json.JSONDecodeError, AttributeError):
            logger.warning(
                "Writer output for %s was not valid JSON, using raw content",
                module_path,
            )
            return CompassDraft(
                quick_commands=content,
                key_files=[module_path],
            )

    def run(self, module: CodeModule) -> CompassDraft:
        initial_state: PipelineState = {
            "source_module": module.file_path,
            "raw_content": module.raw_content,
            "explored": None,
            "analysed": None,
            "written": None,
            "critique": None,
            "retries": 0,
        }

        final_state = self._graph.invoke(initial_state)

        return self._parse_writer_output(
            final_state["written"].content,
            module.file_path,
        )
