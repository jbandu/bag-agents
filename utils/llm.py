"""
LLM client management for Claude (Anthropic) and OpenAI.
"""

import logging
from typing import Any, Dict, List, Optional
from enum import Enum

from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from pydantic_settings import BaseSettings


logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"


class LLMConfig(BaseSettings):
    """LLM configuration from environment variables."""

    anthropic_api_key: Optional[str] = None
    openai_api_key: Optional[str] = None
    default_llm_model: str = "claude-3-5-sonnet-20241022"
    default_temperature: float = 0.7
    max_tokens: int = 4096

    class Config:
        env_file = ".env"
        case_sensitive = False


class LLMClient:
    """
    Unified LLM client for interacting with Claude and OpenAI.

    Supports:
    - Text generation
    - Embeddings
    - Streaming responses
    - Provider switching
    """

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        Initialize LLM client.

        Args:
            config: LLM configuration (loaded from env if not provided)
        """
        self.config = config or LLMConfig()
        self.logger = logging.getLogger(__name__)

        # Initialize clients
        self._anthropic_client: Optional[ChatAnthropic] = None
        self._openai_client: Optional[ChatOpenAI] = None
        self._embeddings_client: Optional[OpenAIEmbeddings] = None

    def get_anthropic_client(
        self,
        model: Optional[str] = None,
        temperature: Optional[float] = None
    ) -> ChatAnthropic:
        """
        Get or create Anthropic (Claude) client.

        Args:
            model: Model name (defaults to config default)
            temperature: Temperature for generation

        Returns:
            ChatAnthropic client instance
        """
        if not self.config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        model = model or self.config.default_llm_model
        temperature = temperature if temperature is not None else self.config.default_temperature

        return ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.config.anthropic_api_key
        )

    def get_openai_client(
        self,
        model: str = "gpt-4",
        temperature: Optional[float] = None
    ) -> ChatOpenAI:
        """
        Get or create OpenAI client.

        Args:
            model: Model name
            temperature: Temperature for generation

        Returns:
            ChatOpenAI client instance
        """
        if not self.config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")

        temperature = temperature if temperature is not None else self.config.default_temperature

        return ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=self.config.max_tokens,
            api_key=self.config.openai_api_key
        )

    def get_embeddings_client(
        self,
        model: str = "text-embedding-3-small"
    ) -> OpenAIEmbeddings:
        """
        Get or create OpenAI embeddings client.

        Args:
            model: Embedding model name

        Returns:
            OpenAIEmbeddings client instance
        """
        if not self.config.openai_api_key:
            raise ValueError("OPENAI_API_KEY not set")

        if not self._embeddings_client:
            self._embeddings_client = OpenAIEmbeddings(
                model=model,
                api_key=self.config.openai_api_key
            )

        return self._embeddings_client

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> str:
        """
        Generate text using specified LLM provider.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            provider: LLM provider to use
            model: Model name (provider-specific)
            temperature: Temperature for generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
            if provider == LLMProvider.ANTHROPIC:
                client = self.get_anthropic_client(model=model, temperature=temperature)
            elif provider == LLMProvider.OPENAI:
                client = self.get_openai_client(model=model or "gpt-4", temperature=temperature)
            else:
                raise ValueError(f"Unsupported provider: {provider}")

            response = await client.ainvoke(messages, **kwargs)
            return response.content

        except Exception as e:
            self.logger.error(f"LLM generation error: {e}")
            raise

    async def generate_with_context(
        self,
        messages: List[Dict[str, str]],
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate text with conversation context.

        Args:
            messages: List of message dicts with 'role' and 'content'
            provider: LLM provider to use
            model: Model name
            **kwargs: Additional parameters

        Returns:
            Generated text
        """
        formatted_messages = []

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                formatted_messages.append(SystemMessage(content=content))
            elif role == "user":
                formatted_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                formatted_messages.append(AIMessage(content=content))

        try:
            if provider == LLMProvider.ANTHROPIC:
                client = self.get_anthropic_client(model=model)
            else:
                client = self.get_openai_client(model=model or "gpt-4")

            response = await client.ainvoke(formatted_messages, **kwargs)
            return response.content

        except Exception as e:
            self.logger.error(f"LLM generation with context error: {e}")
            raise

    async def generate_embeddings(
        self,
        texts: List[str],
        model: str = "text-embedding-3-small"
    ) -> List[List[float]]:
        """
        Generate embeddings for a list of texts.

        Args:
            texts: List of text strings
            model: Embedding model name

        Returns:
            List of embedding vectors
        """
        try:
            embeddings_client = self.get_embeddings_client(model=model)
            embeddings = await embeddings_client.aembed_documents(texts)
            return embeddings

        except Exception as e:
            self.logger.error(f"Embedding generation error: {e}")
            raise

    async def stream_generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        provider: LLMProvider = LLMProvider.ANTHROPIC,
        model: Optional[str] = None,
        **kwargs
    ):
        """
        Stream generated text.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt
            provider: LLM provider to use
            model: Model name
            **kwargs: Additional parameters

        Yields:
            Text chunks as they are generated
        """
        messages = []

        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        messages.append(HumanMessage(content=prompt))

        try:
            if provider == LLMProvider.ANTHROPIC:
                client = self.get_anthropic_client(model=model)
            else:
                client = self.get_openai_client(model=model or "gpt-4")

            async for chunk in client.astream(messages, **kwargs):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content

        except Exception as e:
            self.logger.error(f"LLM streaming error: {e}")
            raise


# Singleton instance
_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    Get or create the singleton LLMClient instance.

    Returns:
        LLMClient instance
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
