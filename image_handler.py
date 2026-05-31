import base64
import os

from anthropic import Anthropic
from openai import OpenAI

_anthropic: Anthropic | None = None
_openai: OpenAI | None = None

ENHANCER_MODEL = "claude-sonnet-4-6"
IMAGE_MODEL = "gpt-image-1"  # dall-e-3 not available on this key; gpt-image-1 confirmed working

_ENHANCER_SYSTEM = (
    "You are Xovia AI, an expert image prompt engineer. "
    "Never mention Claude, Anthropic, OpenAI, or any underlying AI provider. "
    "Take the user's image request and rewrite it as a detailed, specific prompt "
    "that will produce a high quality result. "
    "Return only the enhanced prompt, nothing else. No explanation, no preamble."
)


def _get_anthropic() -> Anthropic:
    global _anthropic
    if _anthropic is None:
        _anthropic = Anthropic()
    return _anthropic


def _get_openai() -> OpenAI:
    global _openai
    if _openai is None:
        _openai = OpenAI()
    return _openai


def enhance_prompt(raw: str) -> str:
    response = _get_anthropic().messages.create(
        model=ENHANCER_MODEL,
        max_tokens=512,
        system=_ENHANCER_SYSTEM,
        messages=[{"role": "user", "content": raw}],
    )
    return response.content[0].text.strip()


def generate_image(prompt: str) -> tuple[bytes | None, str, str | None]:
    """
    Enhance prompt via Claude, generate via gpt-image-1, decode b64 to bytes.
    Returns (image_bytes, enhanced_prompt, error_key).
    error_key is None on success, "content_policy" or "api_error" on failure.
    """
    try:
        enhanced = enhance_prompt(prompt)
    except Exception:
        enhanced = prompt  # fall back to raw prompt if enhancement fails

    try:
        response = _get_openai().images.generate(
            model=IMAGE_MODEL,
            prompt=enhanced,
            size="1024x1024",
            n=1,
        )
        img_bytes = base64.b64decode(response.data[0].b64_json)
        return img_bytes, enhanced, None

    except Exception as e:
        err = str(e).lower()
        if any(kw in err for kw in ("content_policy", "safety", "declined", "rejected")):
            return None, enhanced, "content_policy"
        return None, enhanced, "api_error"


# ---------------------------------------------------------------------------
# Standalone test — run with: python image_handler.py
# Saves generated images to test_output_1.png, test_output_2.png, test_output_3.png
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import tomllib

    with open(".streamlit/secrets.toml", "rb") as f:
        _secrets = tomllib.load(f)
    os.environ["ANTHROPIC_API_KEY"] = _secrets["anthropic"]["api_key"]
    os.environ["OPENAI_API_KEY"] = _secrets["openai"]["api_key"]

    test_prompts = [
        "make a logo for a coffee shop called Brew & Co, minimal style",
        "a futuristic city skyline at sunset",
        "a cartoon dog wearing a business suit",
    ]

    for i, raw in enumerate(test_prompts, 1):
        print(f"\n[{i}] Original : {raw}")
        img_bytes, enhanced, error = generate_image(raw)
        if error:
            print(f"    ERROR   : {error}")
        else:
            out = f"test_output_{i}.png"
            with open(out, "wb") as fh:
                fh.write(img_bytes)
            print(f"    Enhanced: {enhanced[:120]}...")
            print(f"    Saved   : {out} ({len(img_bytes):,} bytes)")
