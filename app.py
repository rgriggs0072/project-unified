import os
from io import BytesIO

import streamlit as st
from PIL import Image

# set_page_config MUST be the first Streamlit call.
# If it comes after any import that can fail, Streamlit shows a raw
# error screen on cold-start before recovering — the one-frame flash.
st.set_page_config(
    page_title="Xovia",
    page_icon="⚡",
    layout="wide",
)

# Inject secrets into env so lazy API clients can find the keys.
try:
    os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["anthropic"]["api_key"])
    os.environ.setdefault("OPENAI_API_KEY", st.secrets["openai"]["api_key"])
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

# Local imports after page config — any failure is now caught inside
# the configured page rather than on a blank error screen.
from xovia_config import get_display_label, get_icon  # noqa: E402
from handlers import stream_chat, stream_code  # noqa: E402
from image_handler import generate_followup_image, generate_image  # noqa: E402
from router import classify  # noqa: E402
from utils import (  # noqa: E402
    detect_document_type,
    detect_language,
    extract_code_block,
    extract_markdown_table_to_csv,
    generate_filename,
    pre_code_text,
    text_to_docx,
)

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
defaults = {
    "messages": [],
    "has_first_message": False,
    "current_route_category": None,
    "last_image_prompt": None,
    "last_image_bytes": None,
    "image_turn_count": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

user_input: str | None = st.chat_input("Ask anything…")

# ---------------------------------------------------------------------------
# Sidebar — about
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("---")
    st.caption("Powered by leading AI models")
    with st.expander("ℹ️ How it works"):
        st.markdown(
            "Xovia routes your requests to the best available AI models to get you "
            "the best result. We use industry-leading language and image models under "
            "the hood so you don't have to think about it.\n\n"
            "Just type — Xovia handles the rest."
        )

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
OVERRIDE_OPTIONS = [
    "🔀 Auto-route",
    "Xovia AI",
    "Xovia AI — Code",
    "Xovia AI — Image",
    "Xovia AI — Cowork",
    "Xovia AI — Analysis",
]

OVERRIDE_TO_CATEGORY: dict[str, str] = {
    "Xovia AI":             "chat",
    "Xovia AI — Code":      "code",
    "Xovia AI — Image":     "image",
    "Xovia AI — Cowork":    "agentic",
    "Xovia AI — Analysis":  "data",
}


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
    _cat = st.session_state.current_route_category
    if _cat:
        _icon = get_icon(_cat)
        _lbl  = get_display_label(_cat)
        pill.markdown(f"**{_icon} {_lbl}**")
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
for _i, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            _msg_cat  = msg.get("category", "chat")
            _msg_icon = get_icon(_msg_cat)
            _msg_lbl  = get_display_label(_msg_cat)
            st.caption(f"{_msg_icon} {_msg_lbl}")

            if _msg_cat in ("image", "image_followup") and msg.get("image_bytes"):
                st.image(Image.open(BytesIO(msg["image_bytes"])), width=512)
                st.caption(f"✨ Enhanced prompt: {msg.get('enhanced_prompt', '')}")
                st.download_button(
                    label="⬇️ Download Image",
                    data=msg["image_bytes"],
                    file_name=generate_filename(msg.get("enhanced_prompt", "image")),
                    mime="image/png",
                    key=f"img_dl_{_i}",
                )
            elif _msg_cat == "code":
                _code, _lang = extract_code_block(msg["content"])
                if _code:
                    _prose = pre_code_text(msg["content"])
                    if _prose:
                        st.markdown(_prose)
                    st.code(_code, language=detect_language(_lang))
                else:
                    st.markdown(msg["content"])
            elif _msg_cat == "data":
                st.markdown(msg["content"])
                _csv = extract_markdown_table_to_csv(msg["content"]) or msg["content"]
                st.download_button(
                    label="📊 Download as .csv",
                    data=_csv,
                    file_name="analysis.csv",
                    mime="text/csv",
                    key=f"dl_{_i}",
                )
            else:
                st.markdown(msg["content"])
                if msg.get("is_document"):
                    st.download_button(
                        label="📄 Download as .docx",
                        data=text_to_docx(msg["content"]),
                        file_name=msg.get("doc_filename", "document.docx"),
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_{_i}",
                    )
        else:
            st.write(msg["content"])


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
            has_image_context = bool(st.session_state.get("last_image_prompt"))
            result = classify(user_input, has_image_context=has_image_context)
            category = result.get("category", "chat")

        # Reset image turn counter whenever we leave the image flow
        if category not in ("image", "image_followup"):
            st.session_state["image_turn_count"] = 0

        # Update session state and pill with Xovia branding
        st.session_state.current_route_category = category
        _icon = get_icon(category)
        _lbl  = get_display_label(category)
        pill.markdown(f"**{_icon} {_lbl}**")
        st.caption(f"{_icon} {_lbl}")

        image_bytes: bytes | None = None
        enhanced_prompt: str = ""
        is_document: bool = False
        doc_filename: str = ""

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

        elif category == "image_followup":
            _last = st.session_state.get("last_image_prompt", "")
            st.caption("🔄 Modifying previous image…")
            with st.spinner("Updating image with your changes…"):
                image_bytes, enhanced_prompt, img_error = generate_followup_image(user_input, _last)
            if img_error == "content_policy":
                st.error("That image request was declined by our content filter — try a different description")
                full_response = "[Image generation declined by content filter]"
            elif img_error:
                st.error("Image generation failed — please try again")
                full_response = "[Image generation failed]"
            else:
                st.image(Image.open(BytesIO(image_bytes)), width=512)
                st.caption(f"✨ Enhanced prompt: {enhanced_prompt}")
                st.download_button(
                    label="⬇️ Download Image",
                    data=image_bytes,
                    file_name=generate_filename(enhanced_prompt),
                    mime="image/png",
                )
                full_response = f"[Image updated] {enhanced_prompt}"
                st.session_state["last_image_prompt"] = enhanced_prompt
                st.session_state["last_image_bytes"] = image_bytes
                st.session_state["image_turn_count"] = st.session_state.get("image_turn_count", 0) + 1

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
                st.download_button(
                    label="⬇️ Download Image",
                    data=image_bytes,
                    file_name=generate_filename(enhanced_prompt),
                    mime="image/png",
                )
                full_response = f"[Image generated] {enhanced_prompt}"
                st.session_state["last_image_prompt"] = enhanced_prompt
                st.session_state["last_image_bytes"] = image_bytes
                st.session_state["image_turn_count"] = 1

        elif category in ("video", "audio", "agentic"):
            _stub_labels = {
                "video":   "Xovia AI — Video",
                "audio":   "Xovia AI — Audio",
                "agentic": "Xovia AI — Cowork",
            }
            _stub = _stub_labels.get(category, "This capability")
            st.info(f"**{_stub}** is coming soon. Routing to Xovia AI for now.")
            full_response = st.write_stream(stream_chat(user_input, prev_history))

        else:
            full_response = st.write_stream(stream_chat(user_input, prev_history))
            if category == "data":
                _csv = extract_markdown_table_to_csv(full_response) or full_response
                st.download_button(
                    label="📊 Download as .csv",
                    data=_csv,
                    file_name="analysis.csv",
                    mime="text/csv",
                )
            else:
                is_document, doc_filename = detect_document_type(user_input)
                if is_document:
                    st.download_button(
                        label="📄 Download as .docx",
                        data=text_to_docx(full_response),
                        file_name=doc_filename,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    )

    st.session_state.messages.append({"role": "user", "content": user_input})
    _assistant_msg: dict = {
        "role":        "assistant",
        "content":     full_response,
        "category":    category,
        "is_document": is_document,
        "doc_filename": doc_filename,
    }
    if category == "image" and image_bytes:
        _assistant_msg["image_bytes"]     = image_bytes
        _assistant_msg["enhanced_prompt"] = enhanced_prompt
    st.session_state.messages.append(_assistant_msg)
