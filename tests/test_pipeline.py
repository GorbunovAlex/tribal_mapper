import json

from domain.entities.code_module import CodeModule
from domain.value_objects.agent_message import AgentMessage, AgentStage
from infrastructure.ai.agent_factory import AgentFactory
from infrastructure.ai.base import IAgent
from infrastructure.ai.graph_state import PipelineState
from infrastructure.ai.langgraph_pipeline import LangGraphExtractionPipeline
from infrastructure.ai.nodes import (
    make_analyse_node,
    make_critique_node,
    make_explore_node,
    make_write_node,
)


class FakeAgent(IAgent):
    def __init__(self, response: str, confidence: float = 1.0) -> None:
        self._response = response
        self._confidence = confidence

    def invoke(self, message: AgentMessage) -> AgentMessage:
        return AgentMessage(
            source_module=message.source_module,
            stage=message.stage,
            content=self._response,
            confidence_score=self._confidence,
        )


WRITER_JSON = json.dumps(
    {
        "quick_commands": "make build && make test",
        "key_files": ["src/auth.py", "src/login.py"],
        "non_obvious_patterns": "Uses decorator-based auth",
        "gotchas": "Token refresh is synchronous",
        "see_also": ["src/session.py"],
    }
)


class FakeAgentFactory(AgentFactory):
    def __init__(
        self,
        explore_response: str = "explored content",
        analyse_response: str = "analysed content",
        write_response: str = WRITER_JSON,
        critique_response: str = "critique feedback",
        critique_confidence: float = 0.9,
    ) -> None:
        self._explore = FakeAgent(explore_response)
        self._analyse = FakeAgent(analyse_response)
        self._write = FakeAgent(write_response)
        self._critique = FakeAgent(critique_response, critique_confidence)

    def create_explorer(self) -> IAgent:
        return self._explore

    def create_analyst(self) -> IAgent:
        return self._analyse

    def create_writer(self) -> IAgent:
        return self._write

    def create_critic(self) -> IAgent:
        return self._critique


class TestNodes:
    def test_explore_node(self):
        agent = FakeAgent("explored!")
        node = make_explore_node(agent)
        state: PipelineState = {
            "source_module": "test.py",
            "raw_content": "code here",
            "explored": None,
            "analysed": None,
            "written": None,
            "critique": None,
            "retries": 0,
        }
        result = node(state)
        assert result["explored"].content == "explored!"

    def test_analyse_node(self):
        agent = FakeAgent("analysed!")
        node = make_analyse_node(agent)
        explored_msg = AgentMessage(
            source_module="test.py", stage=AgentStage.EXPLORE, content="data"
        )
        state: PipelineState = {
            "source_module": "test.py",
            "raw_content": "",
            "explored": explored_msg,
            "analysed": None,
            "written": None,
            "critique": None,
            "retries": 0,
        }
        result = node(state)
        assert result["analysed"].content == "analysed!"

    def test_write_node_uses_analysed_on_first_pass(self):
        agent = FakeAgent("written!")
        node = make_write_node(agent)
        analysed_msg = AgentMessage(
            source_module="test.py", stage=AgentStage.ANALYSE, content="analysis"
        )
        state: PipelineState = {
            "source_module": "test.py",
            "raw_content": "",
            "explored": None,
            "analysed": analysed_msg,
            "written": None,
            "critique": None,
            "retries": 0,
        }
        result = node(state)
        assert result["written"].content == "written!"

    def test_critique_node_increments_retries(self):
        agent = FakeAgent("feedback", confidence=0.5)
        node = make_critique_node(agent)
        written_msg = AgentMessage(
            source_module="test.py", stage=AgentStage.WRITE, content="draft"
        )
        state: PipelineState = {
            "source_module": "test.py",
            "raw_content": "",
            "explored": None,
            "analysed": None,
            "written": written_msg,
            "critique": None,
            "retries": 0,
        }
        result = node(state)
        assert result["retries"] == 1
        assert result["critique"].confidence_score == 0.5


class TestLangGraphPipeline:
    def test_full_pipeline_happy_path(self):
        factory = FakeAgentFactory(critique_confidence=0.9)
        pipeline = LangGraphExtractionPipeline(factory, max_retries=2)

        module = CodeModule(file_path="src/auth.py", raw_content="def login(): pass")
        draft = pipeline.run(module)

        assert draft.quick_commands == "make build && make test"
        assert draft.key_files == ["src/auth.py", "src/login.py"]
        assert draft.non_obvious_patterns == "Uses decorator-based auth"
        assert draft.gotchas == "Token refresh is synchronous"
        assert draft.see_also == ["src/session.py"]

    def test_pipeline_retries_on_low_confidence(self):
        call_count = {"critique": 0, "write": 0}

        class CountingCriticAgent(IAgent):
            def invoke(self, message: AgentMessage) -> AgentMessage:
                call_count["critique"] += 1
                # First call low confidence, second high
                conf = 0.5 if call_count["critique"] == 1 else 0.9
                return AgentMessage(
                    source_module=message.source_module,
                    stage=message.stage,
                    content="critique",
                    confidence_score=conf,
                )

        class CountingWriterAgent(IAgent):
            def invoke(self, message: AgentMessage) -> AgentMessage:
                call_count["write"] += 1
                return AgentMessage(
                    source_module=message.source_module,
                    stage=message.stage,
                    content="written",
                    confidence_score=0.0,
                )

        class RetryFactory(FakeAgentFactory):
            def __init__(self):
                self._explore = FakeAgent("explored")
                self._analyse = FakeAgent("analysed")
                self._write = CountingWriterAgent()
                self._critique = CountingCriticAgent()

        factory = RetryFactory()
        pipeline = LangGraphExtractionPipeline(factory, max_retries=3)

        module = CodeModule(file_path="test.py", raw_content="code")
        pipeline.run(module)

        # Writer called twice (initial + 1 retry), critic called twice
        assert call_count["write"] == 2
        assert call_count["critique"] == 2

    def test_pipeline_respects_max_retries(self):
        # Critic always returns low confidence
        factory = FakeAgentFactory(critique_confidence=0.1)
        pipeline = LangGraphExtractionPipeline(factory, max_retries=2)

        module = CodeModule(file_path="test.py", raw_content="code")
        draft = pipeline.run(module)

        # Should still produce a draft (doesn't crash)
        assert draft.quick_commands == "make build && make test"


class TestParseWriterOutput:
    def test_valid_json_parsed(self):
        content = json.dumps(
            {
                "quick_commands": "npm test",
                "key_files": ["index.js"],
                "non_obvious_patterns": "uses monkey-patching",
                "gotchas": "fragile tests",
                "see_also": ["utils.js"],
            }
        )
        draft = LangGraphExtractionPipeline._parse_writer_output(content, "mod.py")
        assert draft.quick_commands == "npm test"
        assert draft.key_files == ["index.js"]
        assert draft.non_obvious_patterns == "uses monkey-patching"
        assert draft.gotchas == "fragile tests"
        assert draft.see_also == ["utils.js"]

    def test_partial_json_fills_defaults(self):
        content = json.dumps({"quick_commands": "make build"})
        draft = LangGraphExtractionPipeline._parse_writer_output(content, "mod.py")
        assert draft.quick_commands == "make build"
        assert draft.key_files == ["mod.py"]
        assert draft.non_obvious_patterns == ""

    def test_invalid_json_falls_back_to_raw(self):
        content = "This is not JSON at all"
        draft = LangGraphExtractionPipeline._parse_writer_output(content, "mod.py")
        assert draft.quick_commands == "This is not JSON at all"
        assert draft.key_files == ["mod.py"]
