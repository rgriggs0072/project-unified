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


_CHAINED_ENHANCER_SYSTEM = (
    "You are Xovia AI, an expert image prompt engineer. "
    "Never mention Claude, Anthropic, OpenAI, or any underlying AI provider. "
    "The user previously generated an image and now wants to modify it. "
    "Rewrite the FULL image prompt incorporating both the original scene and the new modification. "
    "The result must be a complete, standalone prompt — not just the modification. "
    "Return only the enhanced prompt, nothing else. No explanation, no preamble."
)


def enhance_prompt(raw: str) -> str:
    response = _get_anthropic().messages.create(
        model=ENHANCER_MODEL,
        max_tokens=512,
        system=_ENHANCER_SYSTEM,
        messages=[{"role": "user", "content": raw}],
    )
    return response.content[0].text.strip()


def _generate_from_prompt(enhanced: str) -> tuple[bytes | None, str, str | None]:
    """Send an already-enhanced prompt to gpt-image-1 and return bytes."""
    try:
        response = _get_openai().images.generate(
            model=IMAGE_MODEL,
            prompt=enhanced,
            size="1024x1024",
            n=1,
        )
        return base64.b64decode(response.data[0].b64_json), enhanced, None
    except Exception as e:
        err = str(e).lower()
        if any(kw in err for kw in ("content_policy", "safety", "declined", "rejected")):
            return None, enhanced, "content_policy"
        return None, enhanced, "api_error"


def generate_image(prompt: str) -> tuple[bytes | None, str, str | None]:
    """
    Fresh image: enhance prompt via Claude then generate via gpt-image-1.
    Returns (image_bytes, enhanced_prompt, error_key).
    """
    try:
        enhanced = enhance_prompt(prompt)
    except Exception:
        enhanced = prompt
    return _generate_from_prompt(enhanced)


def generate_followup_image(
    new_request: str,
    last_prompt: str,
) -> tuple[bytes | None, str, str | None]:
    """
    Follow-up image: chain previous enhanced prompt + new modification instruction,
    re-enhance with Claude, then generate via gpt-image-1.
    Returns (image_bytes, new_enhanced_prompt, error_key).
    """
    chain_input = (
        f"Original image prompt:\n{last_prompt}\n\n"
        f"New modification instruction:\n{new_request}"
    )
    try:
        enhanced = _get_anthropic().messages.create(
            model=ENHANCER_MODEL,
            max_tokens=512,
            system=_CHAINED_ENHANCER_SYSTEM,
            messages=[{"role": "user", "content": chain_input}],
        ).content[0].text.strip()
    except Exception:
        enhanced = f"{last_prompt}. Additionally: {new_request}"
    return _generate_from_prompt(enhanced)


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
