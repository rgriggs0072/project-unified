# Project Unified

One place for every AI. Type anything in plain English — the system automatically routes your request to the right AI tool.

**Chat, code, images, data analysis — all in one interface. No tool selection required.**

## What It Does

- **Auto-routes** every prompt using a Claude-powered classifier (chat · code · image · data · and more)
- **Streams responses live** — prose appears as it generates, code snaps into a syntax-highlighted block with a copy button
- **Shows its work** — a routing pill tells you exactly which AI handled your request
- **Manual override** — change the route any time via the dropdown in the top bar

## Running Locally

**1. Clone and install**
```bash
git clone https://github.com/YOUR_USERNAME/project-unified.git
cd project-unified
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
```

**2. Add your API keys**

Create `.streamlit/secrets.toml`:
```toml
[anthropic]
api_key = "sk-ant-..."

[openai]
api_key = "sk-proj-..."
```

**3. Run**
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501).

## Deploying to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect the repo
3. Set your secrets under **Settings → Secrets** — paste the same `secrets.toml` content from above
4. Deploy

Streamlit Cloud reads `requirements.txt` automatically — no extra configuration needed.

## Project Structure

```
app.py          # Streamlit UI — routing pill, chat history, code rendering
router.py       # LLM classifier — returns JSON category for every prompt
handlers.py     # Claude Chat and Claude Code streaming handlers
utils.py        # extract_code_block, detect_language, pre_code_text
```

## Phase Roadmap

| Phase | Status | Scope |
|---|---|---|
| 1 — Prototype | ✅ Done | Router · Chat · Code · Streamlit UI |
| 2 — Image & Data | Planned | DALL-E image gen · data analysis handler |
| 3 — Persistence & Billing | Planned | Snowflake history · Stripe billing · user accounts |

## Stack

- Python 3.11 · Streamlit 1.58
- Anthropic API (Claude Sonnet 4.6) — router + chat + code
- OpenAI API — image generation (Phase 2)
