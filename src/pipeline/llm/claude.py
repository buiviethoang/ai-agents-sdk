"""LLM chat helpers (truncate, send)."""
import logging

from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"
DEFAULT_MODEL_OPENAI = "claude-sonnet-4.6"
MAX_TOKENS = 4096
CHARS_PER_TOKEN = 4
MAX_INPUT_CHARS = 45000


def truncate(s: str, max_chars: int) -> str:
    if len(s) <= max_chars:
        return s
    return s[:max_chars] + "\n...(truncated)"


def send(model, system: str, user: str, verbose: bool = False) -> str:
    system = truncate(system, MAX_INPUT_CHARS)
    user = truncate(user, MAX_INPUT_CHARS)

    messages = []
    if system:
        messages.append(SystemMessage(content=system))
    messages.append(HumanMessage(content=user))

    if verbose:
        logger.info("LLM request system=%d user=%d", len(system), len(user))

    response = model.invoke(messages)

    if verbose:
        logger.info("LLM response %d chars", len(response.content))

    return response.content if hasattr(response, "content") else str(response)
