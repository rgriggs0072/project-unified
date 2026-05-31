import os

import streamlit as st

# Inject Streamlit secrets into env before any API client is created
try:
    os.environ.setdefault("ANTHROPIC_API_KEY", st.secrets["anthropic"]["api_key"])
    os.environ.setdefault("OPENAI_API_KEY", st.secrets["openai"]["api_key"])
except Exception:
    from dotenv import load_dotenv
    load_dotenv()

from handlers import stream_chat, stream_code  # noqa: E402
from router import CATEGORY_LABELS, classify, route_label  # noqa: E402
from utils import detect_language, extract_code_block, pre_code_text  # noqa: E402

st.set_page_config(
    page_title="Project Unified",
    page_icon="⚡",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Session state bootstrap
# ---------------------------------------------------------------------------
defaults = {
    "messages": [],           # list of {role, content, route?, category?}
    "has_first_message": False,
    "current_route_label": None,
    "pending_input": None,    # set by hint-chip buttons
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------------------------------------------------------
# Capture inputs at the top so they're available during render
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

# st.chat_input is always sticky-bottom but its value is available here
raw_chat_input: str | None = st.chat_input("Ask anything…")

# Consume a pending chip input (set by button press on previous run)
user_input: str | None = raw_chat_input
if not user_input and st.session_state.pending_input:
    user_input = st.session_state.pending_input
    st.session_state.pending_input = None

# ---------------------------------------------------------------------------
# Top bar: title | override selectbox | routing pill
# ---------------------------------------------------------------------------
col_title, col_override, col_pill = st.columns([3, 2, 2])

with col_title:
    st.markdown("## ⚡ Project Unified")

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
# Empty state — hero (disappears after first message)
# ---------------------------------------------------------------------------
if not st.session_state.has_first_message:
    st.markdown("# Ask anything. We'll find the right AI.")
    st.markdown("Chat, code, images, analysis — all in one place.")

# ---------------------------------------------------------------------------
# Chat history (all previous messages)
# ---------------------------------------------------------------------------
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        if msg["role"] == "assistant":
            st.caption(f"Routed to {msg.get('route', 'unknown')}")
            _code, _lang = extract_code_block(msg["content"])
            if _code and msg.get("category") == "code":
                _prose = pre_code_text(msg["content"])
                if _prose:
                    st.markdown(_prose)
                st.code(_code, language=detect_language(_lang))
            else:
                st.markdown(msg["content"])
        else:
            st.write(msg["content"])

# ---------------------------------------------------------------------------
# Hint chips — always visible, below history
# ---------------------------------------------------------------------------
CHIPS: list[tuple[str, str]] = [
    ("✍️ Write me a cover letter", "Write me a cover letter for a software engineering role."),
    ("🐍 Debug my Python code", "Help me debug my Python code."),
    ("🖼️ Make an image of...", "Make an image of a futuristic city at sunset."),
    ("📊 Summarize this CSV", "Summarize the key insights from this CSV dataset."),
]

chip_cols = st.columns(len(CHIPS))
for col, (label, prompt) in zip(chip_cols, CHIPS):
    with col:
        if st.button(label, use_container_width=True):
            st.session_state.pending_input = prompt
            st.rerun()

# ---------------------------------------------------------------------------
# Process new input
# ---------------------------------------------------------------------------
if user_input:
    st.session_state.has_first_message = True

    # Snapshot history before appending (handlers build messages from history + prompt)
    prev_history = list(st.session_state.messages)

    # Render the new user message inline
    with st.chat_message("user"):
        st.write(user_input)

    with st.chat_message("assistant"):
        # Phase 1 of pill: show routing spinner
        pill.markdown("**⏳ Routing…**")

        # Determine route
        if override != "🔀 Auto-route":
            category = OVERRIDE_TO_CATEGORY.get(override, "chat")
        else:
            result = classify(user_input)
            category = result.get("category", "chat")

        route_name = route_label(category)
        st.session_state.current_route_label = route_name

        # Phase 2 of pill: snap to actual route
        pill.markdown(f"**⚡ {route_name}**")

        # Per-message route tag
        st.caption(f"Routed to {route_name}")

        # ---------------------------------------------------------------
        # Stream + render response
        # ---------------------------------------------------------------
        if category == "code":
            stream_slot = st.empty()

            # Stream into the slot (shows live prose + raw code fences)
            with stream_slot.container():
                full_response: str = st.write_stream(
                    stream_code(user_input, prev_history)
                )

            # Re-render: replace raw streamed markdown with formatted code block
            code_block, lang_hint = extract_code_block(full_response)
            if code_block:
                prose = pre_code_text(full_response)
                stream_slot.empty()
                with stream_slot.container():
                    if prose:
                        st.markdown(prose)
                    st.code(code_block, language=detect_language(lang_hint))
            # If no code block found, the streamed markdown stays as-is

        elif category in ("image", "video", "audio", "agentic"):
            # Phase-2 stubs — give the user a clear "coming soon" message
            _stub_labels = {
                "image": "Image generation",
                "video": "Video generation",
                "audio": "Audio generation",
                "agentic": "Cowork (agentic tasks)",
            }
            _label = _stub_labels.get(category, category.title())
            st.info(f"**{_label}** is coming in Phase 2. Routing to Claude Chat for now.")
            full_response = st.write_stream(stream_chat(user_input, prev_history))

        else:
            # chat / data / fallback
            full_response = st.write_stream(stream_chat(user_input, prev_history))

    # Persist both turns to session state
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": full_response,
            "route": route_name,
            "category": category,
        }
    )
