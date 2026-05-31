import re


def extract_code_block(text: str) -> tuple[str, str]:
    """Extract the first fenced code block. Returns (code, language)."""
    match = re.search(r"```(\w*)\n(.*?)```", text, re.DOTALL)
    if match:
        lang = match.group(1).strip() or "text"
        code = match.group(2).rstrip()
        return code, lang
    return "", ""


def detect_language(fence_hint: str) -> str:
    """Normalize a code-fence language hint to a Streamlit-recognized token."""
    _map = {
        "py": "python",
        "js": "javascript",
        "ts": "typescript",
        "sh": "bash",
        "shell": "bash",
        "zsh": "bash",
        "rb": "ruby",
        "rs": "rust",
        "": "text",
    }
    hint = fence_hint.lower().strip()
    return _map.get(hint, hint or "text")


def pre_code_text(text: str) -> str:
    """Return the text that appears before the first code fence."""
    idx = text.find("```")
    if idx == -1:
        return text.strip()
    return text[:idx].strip()
