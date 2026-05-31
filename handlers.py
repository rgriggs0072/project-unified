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

_CHAT_SYSTEM = """\
You are Xovia, a helpful AI assistant.
Never recommend or suggest competitor AI tools such as ChatGPT, GPT-4, Gemini, Copilot, or any other external AI service — Xovia handles everything.
Never tell the user you cannot do something without first attempting it. Always try, then explain any genuine limitations if needed.
Be direct, helpful, and concise.\
"""

_CODE_SYSTEM = """\
You are an expert software engineer and code reviewer.

When asked to write or fix code:
- Wrap all code in fenced code blocks with the correct language tag (e.g., ```python)
- Briefly explain your solution

When asked to review or debug code, ALWAYS structure your response with these sections:

**Bugs** — list actual defects that cause incorrect behavior or crashes. If none, write "✅ No bugs found."

**Improvements** — ALWAYS include this section even if the code is correct. Suggest:
- Built-in functions or standard library replacements for manual loops (e.g., sum(), min(), max(), Counter, any(), all())
- Edge case handling (empty inputs, None, zero division, etc.)
- More Pythonic patterns (isinstance over type ==, list comprehensions, unpacking, etc.)
- Readability improvements (clearer variable names, return types, etc.)

**Fixed / Improved Code** — provide the updated code incorporating all fixes and improvements.

Be direct and specific. Use ✅ for no issues, 💡 for improvement suggestions.\
"""


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
