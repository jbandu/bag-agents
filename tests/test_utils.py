"""
Tests for utility modules.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from utils.llm import LLMClient, LLMProvider
from utils.monitoring import track_api_request, track_agent_execution


def test_llm_client_initialization():
    """Test LLMClient initialization."""
    with patch("utils.llm.LLMConfig") as mock_config:
        mock_config.return_value.anthropic_api_key = "test-key"
        mock_config.return_value.openai_api_key = "test-key"

        client = LLMClient()

        assert client.config is not None


def test_llm_client_get_anthropic():
    """Test getting Anthropic client."""
    with patch("utils.llm.LLMConfig") as mock_config:
        mock_config.return_value.anthropic_api_key = "test-key"
        mock_config.return_value.default_llm_model = "claude-3-5-sonnet-20241022"
        mock_config.return_value.default_temperature = 0.7
        mock_config.return_value.max_tokens = 4096

        client = LLMClient()

        with patch("utils.llm.ChatAnthropic") as mock_anthropic:
            anthropic_client = client.get_anthropic_client()
            mock_anthropic.assert_called_once()


def test_llm_client_get_openai():
    """Test getting OpenAI client."""
    with patch("utils.llm.LLMConfig") as mock_config:
        mock_config.return_value.openai_api_key = "test-key"
        mock_config.return_value.default_temperature = 0.7
        mock_config.return_value.max_tokens = 4096

        client = LLMClient()

        with patch("utils.llm.ChatOpenAI") as mock_openai:
            openai_client = client.get_openai_client()
            mock_openai.assert_called_once()


def test_llm_client_missing_api_key():
    """Test LLMClient with missing API key."""
    with patch("utils.llm.LLMConfig") as mock_config:
        mock_config.return_value.anthropic_api_key = None
        mock_config.return_value.openai_api_key = None

        client = LLMClient()

        with pytest.raises(ValueError, match="ANTHROPIC_API_KEY not set"):
            client.get_anthropic_client()

        with pytest.raises(ValueError, match="OPENAI_API_KEY not set"):
            client.get_openai_client()


@pytest.mark.asyncio
async def test_llm_generate():
    """Test LLM text generation."""
    with patch("utils.llm.LLMConfig") as mock_config:
        mock_config.return_value.anthropic_api_key = "test-key"
        mock_config.return_value.default_llm_model = "claude-3-5-sonnet-20241022"
        mock_config.return_value.default_temperature = 0.7
        mock_config.return_value.max_tokens = 4096

        client = LLMClient()

        with patch.object(client, "get_anthropic_client") as mock_get_client:
            mock_llm = Mock()
            mock_llm.ainvoke = AsyncMock(return_value=Mock(content="Generated text"))
            mock_get_client.return_value = mock_llm

            result = await client.generate(
                prompt="Test prompt",
                provider=LLMProvider.ANTHROPIC
            )

            assert result == "Generated text"
            mock_llm.ainvoke.assert_called_once()


def test_monitoring_track_api_request():
    """Test API request tracking."""
    # This should not raise any exceptions
    track_api_request("GET", "/test", 200, 0.5)


def test_monitoring_track_agent_execution():
    """Test agent execution tracking."""
    # This should not raise any exceptions
    track_agent_execution("test_agent", "success", 1.0)


def test_database_config():
    """Test database configuration."""
    from utils.database import DatabaseConfig

    with patch.dict("os.environ", {
        "NEON_DB_HOST": "test-host",
        "NEON_DB_PORT": "5432",
        "NEON_DB_NAME": "test-db",
        "NEON_DB_USER": "test-user",
        "NEON_DB_PASSWORD": "test-pass",
        "NEO4J_URI": "bolt://localhost:7687",
        "NEO4J_USER": "neo4j",
        "NEO4J_PASSWORD": "password"
    }):
        config = DatabaseConfig()

        assert config.neon_db_host == "test-host"
        assert config.neon_db_port == 5432
        assert config.neo4j_uri == "bolt://localhost:7687"
