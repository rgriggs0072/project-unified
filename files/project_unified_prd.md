# Project Unified — Product Requirements Document
**Version:** 0.1 (MVP)
**Author:** PM Session
**Status:** Draft
**Last Updated:** May 2026

---

## Problem Statement

Non-technical and business users want to leverage AI but face a fragmented landscape of tools — Claude, ChatGPT, Midjourney, Runway, code assistants, agentic platforms — each with its own interface, learning curve, and subscription cost. Users don't know which AI to use for which task, so they either pick the wrong one, miss better options, or give up entirely. Project Unified solves this by providing a single conversational interface that automatically routes any request to the right AI tool — removing the expertise barrier and the subscription management burden entirely.

---

## Goals

1. **Routing accuracy**: Auto-router correctly identifies the right AI tool category for ≥90% of user requests without manual override.
2. **Time to first value**: A new user can submit their first successfully routed request within 60 seconds of landing on the platform.
3. **User retention**: 50% of users return within 7 days of first use.
4. **Monetization**: Cover underlying LLM/API costs within 60 days of launch via freemium conversion.
5. **Breadth of coverage**: MVP supports at least 4 distinct AI capability categories (chat, code, image, agentic/cowork).

---

## Non-Goals

1. **Building our own AI models** — Project Unified is a router and interface layer, not an AI research company. We rely entirely on third-party APIs.
2. **Mobile app at launch** — Browser + desktop first. Mobile is v2.
3. **Enterprise SSO / team management** — Individual and small group use only at launch. Enterprise auth is a separate initiative.
4. **Real-time collaboration** — Multiple users working in the same session is out of scope for MVP.
5. **Training or fine-tuning models on user data** — Privacy-first; we do not retain or train on user prompts at launch.

---

## User Personas

### Persona 1: The Curious Non-Technical User ("Maya")
- Has heard about AI but finds it overwhelming
- Doesn't know the difference between Claude, ChatGPT, Midjourney
- Wants to use AI to write emails, make images, summarize documents
- Will abandon if she has to make decisions she doesn't understand

### Persona 2: The Business Power User ("Carlos")
- Comfortable with software, uses AI occasionally but inefficiently
- Switches between 3-4 different AI tools daily
- Frustrated by multiple subscriptions and context-switching
- Wants one place that handles everything and doesn't slow him down

### Persona 3: The Developer / Technical User ("Priya")
- Uses Claude Code or GitHub Copilot regularly
- Wants agentic capabilities (Cowork-style multi-step tasks)
- Appreciates override controls and visibility into which model was used
- Will use Project Unified if it saves time and doesn't get in the way

---

## User Stories

### Routing & Core Experience
- As Maya, I want to type a question in plain English so that I don't have to know which AI to use.
- As Carlos, I want the system to automatically detect I need an image and route to the right tool so that I don't have to switch apps.
- As Priya, I want to see which AI tool was selected for my request so that I can trust the system and override if needed.
- As any user, I want to override the auto-selected AI and choose a different one so that I stay in control.

### Onboarding
- As Maya, I want a simple onboarding that shows me what the platform can do so that I understand its value immediately.
- As any user, I want to start using the platform without creating an account so that I can try before I commit.

### Subscription & Billing
- As any user, I want a free tier with limited usage so that I can evaluate the platform before paying.
- As Carlos, I want a single monthly subscription that covers all AI tools so that I don't manage separate subscriptions.
- As any user, I want to see how many credits/requests I have remaining so that I'm not surprised by limits.

### Output & History
- As any user, I want to see the output from the routed AI inline in my session so that I don't have to switch windows.
- As Carlos, I want to view my past requests and their outputs so that I can reference previous work.

---

## Requirements

### P0 — Must Have (MVP cannot ship without these)

| # | Requirement | Acceptance Criteria |
|---|---|---|
| P0-1 | **Single input box** — one text field for all requests | User types any prompt; system accepts it regardless of type |
| P0-2 | **AI Router** — classifies request into category (chat, code, image, agentic, data, video, audio) | Given any natural language prompt, system returns a category with ≥90% accuracy on test set |
| P0-3 | **Claude Chat integration** — routes conversational/research/writing requests | Response appears inline within 5 seconds for simple queries |
| P0-4 | **Claude Code integration** — routes coding/debugging requests | Code output rendered with syntax highlighting |
| P0-5 | **Image generation integration** — routes image requests to at least one provider (DALL-E or Stability AI) | Image renders inline in the response panel |
| P0-6 | **Override control** — user can see which AI was selected and change it | Dropdown or pill shows active AI; user can tap to change before or after submission |
| P0-7 | **Freemium account system** — free tier with usage cap, paid tier unlimited (or high cap) | Free users see usage meter; upgrade prompt shown at 80% and 100% of limit |
| P0-8 | **Streamlit web UI** — works in browser | Renders correctly in Chrome, Firefox, Safari |
| P0-9 | **Basic conversation history** — session persists within a single visit | Scroll up to see prior exchanges in current session |

### P1 — Nice to Have (strong fast-follow)

| # | Requirement |
|---|---|
| P1-1 | **Claude Cowork / Agentic routing** — multi-step task execution |
| P1-2 | **Data analysis routing** — CSV upload + analysis via Claude |
| P1-3 | **Persistent history** — conversations saved across sessions |
| P1-4 | **Video generation routing** — Runway or similar |
| P1-5 | **Voice/audio routing** — ElevenLabs or similar |
| P1-6 | **Desktop app** — Electron or Claude Desktop wrapper |
| P1-7 | **Usage dashboard** — show user their request breakdown by AI type |
| P1-8 | **Suggested prompts** — onboarding examples to guide new users |

### P2 — Future Considerations

| # | Requirement |
|---|---|
| P2-1 | Mobile app (iOS/Android) |
| P2-2 | Team/multi-user workspaces |
| P2-3 | Enterprise SSO |
| P2-4 | Custom routing rules (user defines their own routing logic) |
| P2-5 | Plugin/connector marketplace |
| P2-6 | White-label offering for businesses |

---

## Technical Architecture (High Level)

```
User Input
    │
    ▼
[Router LLM — Claude Sonnet]
    │  Classifies into: chat | code | image | agentic | data | video | audio
    ▼
[Dispatcher]
    ├── chat      → Anthropic API (Claude)
    ├── code      → Anthropic API (Claude Code prompt)
    ├── image     → DALL-E 3 / Stability AI API
    ├── agentic   → Claude + tools (browser, file, terminal)
    ├── data      → Claude + code execution
    ├── video     → Runway API
    └── audio     → ElevenLabs API
    │
    ▼
[Response Renderer — Streamlit UI]
    Renders: text | code | image | video | audio inline
```

**Stack:**
- **Frontend/UI:** Streamlit (Python)
- **Router:** Claude Sonnet via Anthropic API (classifier prompt returning JSON)
- **Backend:** Python
- **Database:** Snowflake (conversation history, user accounts, usage tracking)
- **Auth:** Simple email/password MVP → OAuth v2
- **Billing:** Stripe

---

## Monetization Model

Given that underlying API costs are real and ongoing, a **freemium + subscription** model is recommended:

| Tier | Price | Limits | Notes |
|---|---|---|---|
| **Free** | $0 | 20 requests/month | All AI types included; shows upgrade prompts |
| **Pro** | $19/month | 500 requests/month | Priority routing, history, all AI types |
| **Unlimited** | $49/month | Unlimited | Power users, developers |

> **Key principle:** Pricing must cover blended API cost per request. Estimated blended cost per request: ~$0.03–0.15 depending on AI type. At 500 requests, Pro tier covers cost at ~$0.038/request minimum.

---

## Success Metrics

### Leading Indicators (measure weekly)
- % of requests correctly auto-routed (target: ≥90%)
- Time to first successful request for new users (target: <60 seconds)
- Free-to-paid conversion rate (target: ≥5% within 30 days)
- Daily active users (DAU)

### Lagging Indicators (measure monthly)
- 7-day retention rate (target: ≥50%)
- Monthly recurring revenue (MRR) vs. API cost
- Average requests per user per month
- NPS score (target: >40)

---

## Open Questions

| # | Question | Owner | Blocking? |
|---|---|---|---|
| OQ-1 | Which image generation API to use at launch — DALL-E 3 (easier) or Stability AI (cheaper)? | Builder | Yes |
| OQ-2 | How do we handle Cowork routing if Claude Desktop API access is limited? | Builder + Research | Yes |
| OQ-3 | What is the free tier limit that balances acquisition vs. cost? 20 requests? 50? | Builder | Yes |
| OQ-4 | Do we need terms of service / privacy policy before public launch? | Legal/Builder | Yes |
| OQ-5 | Should routing decisions be shown to the user or hidden by default? | Design | No |
| OQ-6 | How do we handle multi-part requests (e.g. "write a blog post AND make an image for it")? | Builder | No |
| OQ-7 | What analytics tool to use for tracking usage (Mixpanel, PostHog, or Snowflake only)? | Builder | No |

---

## Phased Timeline

### Phase 1 — Prototype (Weeks 1–3)
- Router LLM classifier working in Python
- Claude Chat + Claude Code routing functional
- Basic Streamlit UI with single input + response panel
- Hardcoded free/paid tiers (no billing yet)
- **Goal:** Working demo you can show someone

### Phase 2 — MVP (Weeks 4–6)
- Image generation integrated (DALL-E or Stability)
- User accounts + Stripe billing
- Snowflake for usage tracking
- Override control in UI
- Basic session history
- **Goal:** Something real users can pay for

### Phase 3 — V1 Launch (Weeks 7–10)
- Cowork/agentic routing
- Data analysis routing
- Persistent conversation history
- Desktop wrapper
- Onboarding flow
- **Goal:** Public launch, start acquiring users

---

## Next Steps

1. ✅ PRD complete — review and approve
2. 🎨 Design session — sketch the UI/UX flow (Streamlit layout, routing indicator, override control)
3. 🔬 Research spike — validate routing accuracy with test prompts before building
4. 🛠 Build Phase 1 prototype
5. 📝 Write SKILL.md files needed for Cowork integration

---

*Document owner: Project Unified team | Next review: After Phase 1 prototype*
