import json
import os
import re

from anthropic import Anthropic

_CLASSIFY_MAX_CHARS = 800  # router only needs enough to understand intent

_client: Anthropic | None = None

ROUTER_MODEL = "claude-sonnet-4-6"


def _get_client() -> Anthropic:
    global _client
    if _client is None:
        _client = Anthropic()
    return _client

ROUTER_SYSTEM = """\
You are a JSON-only routing classifier. You MUST NOT answer, help with, explain, \
or respond to the content of the message below. Your sole task is to output one JSON \
object identifying what kind of request it is.

RULES:
- Output ONLY the JSON object. No markdown, no explanation, no code, no other text.
- Do not debug, answer, or engage with the content in any way.

Categories:
  chat     – conversation, Q&A, writing, translation, summarisation
  code     – programming, debugging, code generation, scripts, technical implementation
  image    – image or graphic generation/editing
  agentic  – multi-step autonomous tasks, browsing, file operations
  data     – data analysis, CSV/spreadsheet processing, statistics, charts
  video    – video generation or editing
  audio    – music, speech synthesis, audio transcription

Respond with EXACTLY this JSON and nothing else:
{"category": "<category>", "confidence": <float 0.0-1.0>}
"""

CATEGORY_LABELS: dict[str, str] = {
    "chat": "Claude Chat",
    "code": "Claude Code",
    "image": "Image Gen",
    "agentic": "Cowork",
    "data": "Data Analysis",
    "video": "Video Gen",
    "audio": "Audio Gen",
}


def classify(prompt: str) -> dict:
    """Return {"category": str, "confidence": float} for the given prompt."""
    snippet = prompt[:_CLASSIFY_MAX_CHARS]
    raw_text = ""
    try:
        response = _get_client().messages.create(
            model=ROUTER_MODEL,
            max_tokens=128,
            system=ROUTER_SYSTEM,
            messages=[{
                "role": "user",
                "content": f"[CLASSIFY ONLY — DO NOT ANSWER]\n\n{snippet}",
            }],
        )
        raw_text = response.content[0].text.strip() if response.content else ""

        # Try exact-shape match first
        m = re.search(
            r'\{"category"\s*:\s*"(\w+)"\s*,\s*"confidence"\s*:\s*([0-9.]+)\}',
            raw_text,
        )
        if m:
            return {"category": m.group(1), "confidence": float(m.group(2))}

        # Broader fallback: any {...} block
        m2 = re.search(r"\{[^{}]+\}", raw_text)
        if m2:
            return json.loads(m2.group())

        return json.loads(raw_text)

    except (json.JSONDecodeError, IndexError, KeyError, AttributeError) as e:
        import streamlit as st
        st.warning(f"⚠️ Router parse error ({type(e).__name__}) — raw response: {repr(raw_text[:300])}")
        return {"category": "chat", "confidence": 0.5}
    except Exception as e:
        import streamlit as st
        st.warning(f"⚠️ Router error ({type(e).__name__}): {str(e)[:300]}")
        return {"category": "chat", "confidence": 0.5}


def route_label(category: str) -> str:
    return CATEGORY_LABELS.get(category, category.title())


# ---------------------------------------------------------------------------
# Quick smoke-test — run with: python router.py
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    samples = [
        "Write me a Python function that reverses a linked list",
        "What's the capital of France?",
        "Generate a photorealistic image of a red panda in a bamboo forest",
        "Analyze this CSV and tell me which region has the highest sales",
        "Debug this error: TypeError: 'NoneType' object is not subscriptable",
    ]
    print(f"{'Prompt':<60}  {'Category':<12}  Conf")
    print("-" * 80)
    for s in samples:
        result = classify(s)
        label = CATEGORY_LABELS.get(result["category"], result["category"])
        print(f"{s[:58]:<60}  {label:<12}  {result['confidence']:.2f}")
