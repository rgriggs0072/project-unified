import os
from io import BytesIO

import streamlit as st
from PIL import Image

# Inject Streamlit secrets into env before any API client is created
try:
    os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["anthropic"]["api_key"])
    os.environ.setdefault("OPENAI_API_KEY", st.secrets["openai"]["api_key"])
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

from handlers import stream_chat, stream_code  # noqa: E402
from image_handler import generate_image  # noqa: E402
from router import CATEGORY_LABELS, classify, route_label  # noqa: E402
from utils import detect_language, extract_code_block, pre_code_text  # noqa: E402

st.set_page_config(
    page_title="Xovia",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
defaults = {
    "messages": [],
    "has_first_message": False,
    "current_route_label": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OVERRIDE_OPTIONS = [
    "🔀 Auto-route",
    "Claude Chat",
    "Claude Code",
    "Image Gen",
    "Cowork",
    "Data Analysis",
]

OVERRIDE_TO_CATEGORY: dict[str, str] = {
    "Claude Chat": "chat",
    "Claude Code": "code",
    "Image Gen": "image",
    "Cowork": "agentic",
    "Data Analysis": "data",
}

CHIPS: list[tuple[str, str]] = [
    ("✍️ Write me a cover letter", "Write me a cover letter for "),
    ("🐍 Debug my Python code", "Debug my Python code: "),
    ("🖼️ Make an image of...", "Make an image of "),
    ("📊 Summarize this CSV", "Summarize this data: "),
]

# ---------------------------------------------------------------------------
# Top bar: title | override selectbox | routing pill
# ---------------------------------------------------------------------------
col_title, col_override, col_pill = st.columns([3, 2, 2])

with col_title:
    st.markdown("## ⚡ Xovia")

with col_override:
    override: str = st.selectbox(
        "Route override",
        options=OVERRIDE_OPTIONS,
        label_visibility="collapsed",
        key="override_select",
    )

with col_pill:
    pill = st.empty()
    if st.session_state.current_route_label:
        pill.markdown(f"**⚡ {st.session_state.current_route_label}**")
    else:
        pill.markdown("*🔀 No route yet*")

st.divider()

# ---------------------------------------------------------------------------
# Empty state hero — disappears after first message
# ---------------------------------------------------------------------------
if not st.session_state.has_first_message:
    st.markdown("# Ask anything. We'll find the right AI.")
    st.markdown("Chat, code, images, analysis — all in one place.")

# ---------------------------------------------------------------------------
# Chat history
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.caption(f"Routed to {msg.get('route', 'unknown')}")
            if msg.get("category") == "image" and msg.get("image_bytes"):
                st.image(Image.open(BytesIO(msg["image_bytes"])), width=512)
                st.caption(f"✨ Enhanced prompt: {msg.get('enhanced_prompt', '')}")
            elif msg.get("category") == "code":
                _code, _lang = extract_code_block(msg["content"])
                if _code:
                    _prose = pre_code_text(msg["content"])
                    if _prose:
                        st.markdown(_prose)
                    st.code(_code, language=detect_language(_lang))
                else:
                    st.markdown(msg["content"])
            else:
                st.markdown(msg["content"])
        else:
            st.write(msg["content"])

# ---------------------------------------------------------------------------
# Hint chips
# Chips MUST appear above the text_input in the script. When a chip is
# clicked, session_state["user_input"] is set and st.rerun() is called.
# The rerun restarts the script from the top; when it reaches the
# text_input, it reads the pre-set session_state value — single click.
# ---------------------------------------------------------------------------
chip_cols = st.columns(len(CHIPS))
for col, (label, prompt) in zip(chip_cols, CHIPS):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state["user_input"] = prompt
            st.rerun()

# ---------------------------------------------------------------------------
# Input box + Send button
# st.form makes Enter and the Send button equivalent.
# clear_on_submit=True resets the field automatically after submission.
# ---------------------------------------------------------------------------
with st.form("chat_form", clear_on_submit=True):
    input_col, send_col = st.columns([9, 1])
    with input_col:
        input_text: str = st.text_input(
            "Ask anything…",
            key="user_input",
            label_visibility="collapsed",
            placeholder="Ask anything…",
        )
    with send_col:
        send_clicked: bool = st.form_submit_button(
            "Send →", type="primary", use_container_width=True
        )

user_input: str | None = input_text.strip() if (send_clicked and input_text.strip()) else None

# ---------------------------------------------------------------------------
# Process submission
# ---------------------------------------------------------------------------
if user_input:
    st.session_state.has_first_message = True
    prev_history = list(st.session_state.messages)

    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        pill.markdown("**⏳ Routing…**")

        if override != "🔀 Auto-route":
            category = OVERRIDE_TO_CATEGORY.get(override, "chat")
        else:
            result = classify(user_input)
            category = result.get("category", "chat")

        route_name = route_label(category)
        st.session_state.current_route_label = route_name
        pill.markdown(f"**⚡ {route_name}**")
        st.caption(f"Routed to {route_name}")

        image_bytes: bytes | None = None
        enhanced_prompt: str = ""

        if category == "code":
            stream_slot = st.empty()
            with stream_slot.container():
                full_response: str = st.write_stream(
                    stream_code(user_input, prev_history)
                )
            code_block, lang_hint = extract_code_block(full_response)
            if code_block:
                prose = pre_code_text(full_response)
                stream_slot.empty()
                with stream_slot.container():
                    if prose:
                        st.markdown(prose)
                    st.code(code_block, language=detect_language(lang_hint))

        elif category == "image":
            with st.spinner("Enhancing prompt and generating image…"):
                image_bytes, enhanced_prompt, img_error = generate_image(user_input)
            if img_error == "content_policy":
                st.error("That image request was declined by our content filter — try a different description")
                full_response = "[Image generation declined by content filter]"
            elif img_error:
                st.error("Image generation failed — please try again")
                full_response = "[Image generation failed]"
            else:
                st.image(Image.open(BytesIO(image_bytes)), width=512)
                st.caption(f"✨ Enhanced prompt: {enhanced_prompt}")
                full_response = f"[Image generated] {enhanced_prompt}"

        elif category in ("video", "audio", "agentic"):
            _stub_labels = {
                "video": "Video generation",
                "audio": "Audio generation",
                "agentic": "Cowork (agentic tasks)",
            }
            _label = _stub_labels.get(category, category.title())
            st.info(f"**{_label}** is coming soon. Routing to Claude Chat for now.")
            full_response = st.write_stream(stream_chat(user_input, prev_history))

        else:
            full_response = st.write_stream(stream_chat(user_input, prev_history))

    st.session_state.messages.append({"role": "user", "content": user_input})
    _assistant_msg: dict = {
        "role": "assistant",
        "content": full_response,
        "route": route_name,
        "category": category,
    }
    if category == "image" and image_bytes:
        _assistant_msg["image_bytes"] = image_bytes
        _assistant_msg["enhanced_prompt"] = enhanced_prompt
    st.session_state.messages.append(_assistant_msg)

