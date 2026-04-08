from application.interfaces.code_repository import CodeRepositoryInterface
from application.interfaces.compass_repository import CompassRepositoryInterface
from application.interfaces.extraction_pipeline import ExtractionPipelineInterface
from application.interfaces.relevance_scorer import RelevanceScorerInterface
from application.use_cases.index_codebase import IndexCodebaseUseCase
from application.use_cases.index_module import IndexModuleUseCase
from application.use_cases.route_query import RouteQueryUseCase
from config.interfaces import AppConfig
from config.loader import load_config
from infrastructure.ai.agent_factory import AgentFactory
from infrastructure.ai.embedding_scorer import EmbeddingRelevanceScorer
from infrastructure.ai.langgraph_pipeline import LangGraphExtractionPipeline
from infrastructure.storage.local_fs_repository import LocalFileCompassRepository
from infrastructure.vcs.git_repo_traversal import GitRepoTraversal


class Container:
    def __init__(self, config: AppConfig | None = None) -> None:
        self._config = config or load_config()

        # Infrastructure — wired from config singleton
        self._compass_repo: CompassRepositoryInterface = LocalFileCompassRepository()
        self._code_repo: CodeRepositoryInterface = GitRepoTraversal(
            extensions=set(self._config.extensions)
        )
        self._scorer: RelevanceScorerInterface = EmbeddingRelevanceScorer(
            model=self._config.embedding_model,
            api_key=self._config.openai_api_key,
        )
        self._agent_factory = AgentFactory(
            self._config.agents, api_key=self._config.openai_api_key
        )
        self._pipeline: ExtractionPipelineInterface = LangGraphExtractionPipeline(
            self._agent_factory
        )

        # Use cases — token_ceiling flows from config
        self._index_module = IndexModuleUseCase(
            self._pipeline,
            self._compass_repo,
            token_ceiling=self._config.token_ceiling,
        )
        self._index_codebase = IndexCodebaseUseCase(self._code_repo, self._index_module)
        self._route_query = RouteQueryUseCase(self._compass_repo, self._scorer)

    @property
    def config(self) -> AppConfig:
        return self._config

    @property
    def index_module(self) -> IndexModuleUseCase:
        return self._index_module

    @property
    def index_codebase(self) -> IndexCodebaseUseCase:
        return self._index_codebase

    @property
    def route_query(self) -> RouteQueryUseCase:
        return self._route_query
