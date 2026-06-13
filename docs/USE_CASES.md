# Who is this for? — 5 ways to use it

This is an open-source, **memory-first** Telegram bot you can run in minutes:
free [OpenRouter](https://openrouter.ai) models (with OpenAI/Anthropic direct as
options), long-term per-user memory via [GetMem](https://getmem.ai), voice
input, per-user limits, **Telegram Stars** payments, and a polished **Mini App**
dashboard with full admin controls. Below are five concrete ways people actually
use a project like this — and exactly which built-in features make each one work.

> The thread through all of them: **memory turns a stateless "GPT wrapper" into
> a product that remembers its users** — and the monetization, limits and admin
> tools are already built in, so you ship a *business*, not a prototype.

---

## 1. Indie hacker launching a niche AI assistant 🚀

**Who:** a solo builder who wants to ship a focused AI bot this weekend — a
"travel planner", "study buddy", "recipe coach", whatever.

**Why this:** you don't write any infra. Fork it, set one `SYSTEM_PROMPT` to
define the niche, point it at free models (so your cost starts at **$0**), and
`docker compose up`. Memory makes it feel personal from day one; the Mini App
gives it a real dashboard; Stars payments mean you can charge from day two.

**Features used:** editable system prompt · free-model rotation · GetMem memory ·
Mini App · Stars upgrade tiers.

---

## 2. Coach / creator monetizing their expertise 💼

**Who:** a language teacher, nutritionist, fitness trainer, finance coach, or
content creator who wants a paid AI assistant trained on *their* approach.

**Why this:** the assistant **remembers each client** — goals, progress, past
advice — across sessions, which is what makes coaching feel real. You define the
persona, gate the good stuff behind a **Premium tier** you price yourself, and
manage clients from the admin panel (grant access, set limits, ban abusers).
Per-user **roles** let each client tune the assistant ("be strict with me",
"explain like I'm a beginner").

**Features used:** long-term memory · custom priced tiers · per-user roles ·
admin user management · Telegram Stars.

---

## 3. Community / channel owner adding an AI perk 👥

**Who:** the admin of a Telegram group, channel, or paid community who wants to
add an AI assistant as a member benefit.

**Why this:** give everyone a **free daily quota**, and offer supporters a
**premium** plan with higher limits and better models. Voice messages lower the
barrier to use; the admin tools let you **freeze/ban** bad actors and bump
limits for VIPs — all from inside Telegram or the dashboard. It drives
engagement and adds a revenue stream without leaving the platform your community
already lives on.

**Features used:** free vs premium daily limits · voice transcription · admin
ban/freeze + per-user limit overrides · usage dashboard.

---

## 4. Developer template for building memory-first AI agents 🛠️

**Who:** an engineer who wants a clean, modern reference for an LLM product —
not a 200-line script.

**Why this:** the backend is **ports & adapters + a DI container** — the core
depends on interfaces (`LLMProvider`, `MemoryStore`, `Transcriber`), and swapping
OpenRouter for OpenAI/Anthropic, or the voice service, is a one-line change. It's
a working showcase of the **GetMem SDK**, OpenRouter's multi-model fallback, the
official OpenAI/Anthropic SDKs, async SQLAlchemy + Alembic, FastAPI + a Next.js
Mini App, and Docker/uv — all wired together and tested. Great starting point to
fork and add your own tools, providers, or channels.

**Features used:** the whole architecture — adapters, model router, config store,
migrations, Mini App API, three deploy modes (local / Caddy / Dokploy).

---

## 5. Self-hosted assistant for a team or small business 🏢

**Who:** an SMB or team that wants a private AI helper — internal FAQ, onboarding
buddy, support draft-writer — **on their own server**, not a third-party SaaS.

**Why this:** it runs entirely in Docker on one box (Postgres + bot + API + Mini
App), so **your data stays with you**. Memory personalizes answers per employee;
admins control who has access and how much; voice makes it usable on the go; and
the included Caddy/Dokploy setups give you a real domain with automatic HTTPS.
Point `SYSTEM_PROMPT` at your internal knowledge/policies and you have a private
assistant in an afternoon.

**Features used:** fully self-hosted Docker stack · per-user access & limits ·
memory · admin panel · auto-HTTPS deployment.

---

### Common thread

| You get… | Because of… |
|---|---|
| A bot that **remembers users** | GetMem long-term memory |
| **$0 to start**, resilient replies | free OpenRouter models + multi-provider fallback |
| **Revenue** from day one | Telegram Stars + configurable priced tiers |
| **Control** over abuse & cost | per-user limits, ban/freeze, admin dashboard |
| **Ownership** of your data | self-hosted, one `docker compose up` |

**Try the live demo:** [@getmem_recall_bot](https://t.me/getmem_recall_bot) ·
**Run your own:** see the [README](../README.md).
