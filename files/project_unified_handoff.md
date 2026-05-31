# Project Unified — Session Handoff Document
*Paste this into the first message of the new Project Unified conversation to restore full context.*

---

## What We're Building

**Project Unified** is a single browser/desktop interface where any user — technical or not — can type any request in plain English and the system automatically routes it to the right AI tool. The user never has to know whether they need Claude, an image generator, a code assistant, or an agentic tool. The system figures it out.

**Core value proposition:** One place. Every AI. No expertise required.

---

## Key Decisions Made

### Concept
- An AI router / orchestration layer built on top of existing AI APIs
- Auto-routes to: Claude Chat, Claude Code, Claude Cowork (agentic), image generation, video generation, voice/audio AI, data analysis
- Default behavior: auto-route. User can always see what was selected and override it
- Built with **Python + Streamlit** (UI), **Anthropic API** (router + Claude), **Snowflake** (history + usage), **Stripe** (billing)

### Target Users
- Non-technical everyday users who are scared of AI
- Any business user who wants one place for all AI tools
- Mix of all technical levels
- Browser + desktop at launch

### Business Model
- **Freemium + subscription** (must monetize because of underlying API costs)
- Free tier: 20 requests/month
- Pro: $19/month / 500 requests
- Unlimited: $49/month
- Stripe for billing

### Naming
- Went through 40+ name candidates — all taken in the AI space
- Working name: **Project Unified**
- Final name TBD — recommended approach: go to namecheap.com and search directly for real-time domain availability
- Top unused foreign language concepts still to check: **unifai**, **samla** (Swedish: gather), **ikigai** (taken)

---

## What's Been Built So Far

### ✅ PRD (Complete)
Full Product Requirements Document written and saved. Key contents:
- Problem statement, goals, non-goals
- 3 user personas: Maya (non-technical), Carlos (business power user), Priya (developer)
- Full user stories
- P0/P1/P2 requirements with acceptance criteria
- Technical architecture diagram (Router → Dispatcher → APIs → Streamlit UI)
- Monetization model with cost math
- Success metrics (leading + lagging)
- 7 open questions (OQ-1 through OQ-7)
- 3-phase timeline: Prototype (wks 1-3), MVP (wks 4-6), V1 Launch (wks 7-10)

---

## Phase 1 Prototype Scope (Weeks 1–3)
The minimum to have a working demo:
1. Router LLM classifier (Claude Sonnet → returns JSON category)
2. Claude Chat routing functional
3. Claude Code routing functional
4. Basic Streamlit UI: single input box + response panel + routing indicator
5. Override control (user can change AI selection)

**Not in Phase 1:** Image gen, billing, accounts, history, Cowork

---

## Biggest Open Questions to Resolve First

| # | Question | Why it matters |
|---|---|---|
| OQ-1 | DALL-E 3 vs Stability AI for image gen? | DALL-E easier, Stability cheaper |
| OQ-2 | How to route to Cowork if it's a desktop app, not an API? | May need to simulate with Claude + tools |
| OQ-3 | Free tier limit — 20 requests or 50? | Affects cost vs. acquisition tradeoff |
| OQ-4 | Need ToS/privacy policy before public launch? | Legal requirement |

---

## Recommended Next Steps (in order)

1. 🎨 **Design session** — sketch the Streamlit UI: input box, routing indicator pill, override dropdown, response panel
2. 🔬 **Research spike** — write and test the router classifier prompt with 20–30 real user prompts to validate ≥90% accuracy before building
3. 🛠 **Build Phase 1 prototype** — Python + Streamlit + Anthropic API
4. 📝 **Write SKILL.md files** — define skills needed for Cowork/agentic layer
5. 💳 **Stripe + Snowflake setup** — usage tracking and billing for Phase 2

---

## Team / Roles We Discussed Using
- **PM** — define requirements and scope (done ✅)
- **Design Engineer** — sketch UI/UX flow (next)
- **Research (Chat)** — explore existing tools, validate routing approach
- **Cowork** — write SKILL.md files and handle complex agentic tasks

---

## Competitive Landscape (from research)
- **Unified AI Hub** (unifiedaihub.com) — closest competitor, already doing this with 50+ models. Validates the idea strongly.
- **Nexus** (YC-backed, $4.3M seed) — enterprise AI agent deployment, different angle
- **Convergence.ai** — acquired by Salesforce, agent-focused
- Key differentiator for Project Unified: **simplicity for non-technical users** + **smart auto-routing** vs. competitors that require users to choose

---

*Session conducted: May 2026 | Ready to continue in Project Unified workspace*
