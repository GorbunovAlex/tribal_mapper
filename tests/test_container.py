"""Smoke test — verifies the DI container assembles without errors."""

from unittest.mock import patch

from config.interfaces import AppConfig
from config.loader import reset_config
from infrastructure.di_container import Container


class TestContainer:
    def setup_method(self):
        reset_config()

    def teardown_method(self):
        reset_config()

    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    @patch("infrastructure.ai.llm_agent.ChatOpenAI")
    def test_container_assembles(self, _mock_chat, _mock_embed):
        config = AppConfig()
        container = Container(config=config)

        assert container.index_module is not None
        assert container.index_codebase is not None
        assert container.route_query is not None
        assert container.config is config

    @patch("infrastructure.ai.embedding_scorer.OpenAIEmbeddings")
    @patch("infrastructure.ai.llm_agent.ChatOpenAI")
    def test_properties_return_same_instances(self, _mock_chat, _mock_embed):
        container = Container(config=AppConfig())

        assert container.index_module is container.index_module
        assert container.index_codebase is container.index_codebase
        assert container.route_query is container.route_query
