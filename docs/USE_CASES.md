# Use cases — who it's for & why it's useful

A starting point *or* a finished product. This is an open-source,
**self-hostable, memory-first** Telegram bot you run in one command: free
[OpenRouter](https://openrouter.ai) models (with multi-provider fallback +
OpenAI/Anthropic/Groq/Gemini/Ollama), **long-term per-user memory** via
[GetMem](https://getmem.ai), voice input, **Telegram Stars** payments,
admin-configurable **priced tiers & per-user limits**, per-user roles, and a
**Next.js Mini App** dashboard with admin controls (ban / freeze / limit / grant).

> **The core idea:** memory turns a stateless "GPT wrapper" into a product that
> *remembers its users* — and monetization, limits, voice and admin tooling are
> already built in. You ship a **business**, not a prototype.

## Why it's useful

- **Launch in minutes, not weeks.** One command sets up the bot, API, dashboard,
  database and payments. You skip the plumbing (billing, memory, admin, auth).
- **Costs start at $0.** Free models via OpenRouter with automatic fallback;
  add premium/direct providers only when you want to.
- **It remembers people.** Long-term per-user memory makes replies personal and
  consistent across sessions — the thing that makes an assistant feel real.
- **Monetization is built in.** Telegram Stars checkout + admin-defined priced
  tiers and daily limits, all editable from the dashboard — no Stripe, no
  external billing.
- **You stay in control.** Admin dashboard to grant plans, set per-user limits,
  ban/freeze abusers, manage providers/models, edit the bot's persona, and
  broadcast — plus voice messages and per-user roles for end users.
- **You own it.** Self-hosted in Docker on one box; with local models (Ollama)
  it can run with no external API at all. Your data stays with you.

## Who it's for

### 1. Indie hacker shipping a monetizable AI product 🚀
Set one `SYSTEM_PROMPT` to define a niche ("travel planner", "study buddy"), run
the installer, and you have memory + Stars checkout + tiers + a dashboard on day
one. Validate cheaply on free models, then turn on premium tiers.

### 2. Coach / creator monetizing expertise 💼
A language teacher, nutritionist, trainer or finance coach sells a paid AI
assistant trained on *their* method. It **remembers each client** (goals,
progress, past advice) — the moat for coaching — and you price Premium in Stars,
set limits, and manage clients from the dashboard. Per-user **roles** let each
client tune the assistant ("be strict", "explain like a beginner").

### 3. Community / channel owner adding an AI perk 👥
Give everyone a **free daily quota** and offer supporters a **premium** plan
(higher limits, better models) paid in Stars — keeping money and audience inside
Telegram. Voice lowers the barrier; admin **ban/freeze** and per-user limits keep
abuse and cost in check.

### 4. Developer template for memory-first AI agents 🛠️
A clean, modern reference: **ports & adapters + a DI container**, so swapping the
LLM provider, memory store or voice service is a one-line change. A working
showcase of the GetMem SDK, multi-model fallback, async SQLAlchemy + Alembic,
FastAPI + a Next.js Mini App, Docker/uv — wired together and tested. Fork it and
add your own tools, providers or channels.

### 5. Self-hosted assistant for a team or SMB 🏢
A private helper (internal FAQ, onboarding buddy, support draft-writer) on your
own server. Runs entirely in Docker; with **Ollama/local models** there's no
external API at all. Memory personalizes per employee; admins control access and
limits; bundled Caddy/Dokploy give a real domain with automatic HTTPS.

## What you get

| Capability | Built in |
|---|---|
| Remembers users across sessions | ✅ long-term memory (GetMem) |
| Multiple providers + free models | ✅ OpenRouter + OpenAI/Anthropic/Groq/Gemini/Ollama |
| Monetization | ✅ Telegram Stars + admin-defined priced tiers |
| Limits & moderation | ✅ per-user limits, ban/freeze, admin dashboard |
| Voice & personalization | ✅ voice transcription + per-user roles |
| Ownership & deploy | ✅ self-hosted, one-command Docker, auto-HTTPS option |

---

**Try the live demo:** [@getmem_recall_bot](https://t.me/getmem_recall_bot)
**Run your own in one command:** see the [README](../README.md#-install-in-one-command).
