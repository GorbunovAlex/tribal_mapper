from application.builders.compass_draft_builder import CompassDraftBuilder
from application.interfaces.extraction_pipeline import ExtractionPipelineInterface
from domain.entities.code_module import CodeModule
from domain.entities.compass_draft import CompassDraft
from domain.value_objects.agent_message import AgentMessage, AgentStage
from infrastructure.ai.agent_factory import AgentFactory


class LangGraphExtractionPipeline(ExtractionPipelineInterface):
    def __init__(self, agent_factory: AgentFactory, max_retries: int = 2) -> None:
        self._factory = agent_factory
        self._max_retries = max_retries

    def run(self, module: CodeModule) -> CompassDraft:
        seed = AgentMessage(
            source_module=module.file_path,
            stage=AgentStage.EXPLORE,
            content=module.raw_content,
        )

        explorer = self._factory.create_explorer()
        explored = explorer.invoke(seed)

        analyst = self._factory.create_analyst()
        analysed = analyst.invoke(explored)

        writer = self._factory.create_writer()
        critic = self._factory.create_critic()

        for _ in range(self._max_retries + 1):
            written = writer.invoke(analysed)
            critique = critic.invoke(written)
            if critique.confidence_score >= 0.8:
                break
            analysed = critique

        builder = CompassDraftBuilder()
        builder.add_quick_commands(written.content)
        builder.add_key_files([module.file_path])
        builder.add_patterns(critique.content)
        return builder.build()
