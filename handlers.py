from typing import Generator

from anthropic import Anthropic

_client: Anthropic | None = None

CHAT_MODEL = "claude-sonnet-4-6"


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client
CODE_MODEL = "claude-sonnet-4-6"

_CHAT_SYSTEM = "You are a helpful, concise AI assistant."

_CODE_SYSTEM = (
    "You are an expert software engineer. "
    "When providing code, always wrap it in a fenced code block with the correct language tag "
    "(e.g., ```python). "
    "Briefly explain your solution before or after the code block."
)


def _history_to_messages(history: list[dict], prompt: str) -> list[dict]:
    """Convert session history + current prompt into the Anthropic messages format."""
    messages = [
        {"role": m["role"], "content": m["content"]}
        for m in history
        if m["role"] in ("user", "assistant")
    ]
    messages.append({"role": "user", "content": prompt})
    return messages


def stream_chat(prompt: str, history: list[dict]) -> Generator[str, None, None]:
    """Stream a general chat response token-by-token."""
    with _get_client().messages.stream(
        model=CHAT_MODEL,
        max_tokens=2048,
        system=_CHAT_SYSTEM,
        messages=_history_to_messages(history, prompt),
    ) as stream:
        yield from stream.text_stream


def stream_code(prompt: str, history: list[dict]) -> Generator[str, None, None]:
    """Stream a code-focused response token-by-token."""
    with _get_client().messages.stream(
        model=CODE_MODEL,
        max_tokens=4096,
        system=_CODE_SYSTEM,
        messages=_history_to_messages(history, prompt),
    ) as stream:
        yield from stream.text_stream
