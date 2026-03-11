"""LLM client factory - Anthropic native vs OpenAI-compat (claudible)."""
import os

from langchain_anthropic import ChatAnthropic
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

from pipeline.config import LLM_BASE_URL, LLM_CLIENT
from pipeline.llm.claude import DEFAULT_MODEL, DEFAULT_MODEL_OPENAI, MAX_TOKENS


def _get_anthropic(api_key: str, model: str, max_tokens: int) -> BaseChatModel:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
    return ChatAnthropic(
        api_key=key,
        model=model,
        max_tokens=max_tokens,
    )


def _get_openai(
    api_key: str,
    model: str,
    max_tokens: int,
    base_url: str = "",
) -> BaseChatModel:
    key = api_key or os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY", "")
    url = base_url or LLM_BASE_URL
    return ChatOpenAI(
        api_key=key,
        base_url=url,
        model=model,
        max_tokens=max_tokens,
    )


def get_model(
    api_key: str = "",
    model: str = DEFAULT_MODEL,
    max_tokens: int = MAX_TOKENS,
    client: str = "",
    base_url: str = "",
) -> BaseChatModel:
    c = (client or LLM_CLIENT).lower()
    if c == "openai":
        m = DEFAULT_MODEL_OPENAI if model == DEFAULT_MODEL else model
        return _get_openai(api_key, m, max_tokens, base_url)
    return _get_anthropic(api_key, model, max_tokens)
