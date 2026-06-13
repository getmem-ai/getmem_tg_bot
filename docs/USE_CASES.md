# Who is this for? — use cases & positioning

This is an open-source, **self-hostable, memory-first** Telegram bot you run in
one command: free [OpenRouter](https://openrouter.ai) models (with multi-provider
fallback + OpenAI/Anthropic direct), **long-term per-user memory** via
[GetMem](https://getmem.ai), voice input, **Telegram Stars** payments,
admin-configurable **priced tiers & per-user limits**, per-user roles, and a
polished **Next.js Mini App** dashboard with full admin controls (ban / freeze /
limit / grant).

> **Positioning in one line:** the only open-source Telegram bot that is
> *memory-first, multi-provider, and monetizable out of the box* — with an admin
> dashboard. Today those capabilities exist only **separately** across different
> projects; here they're one `docker compose up`.

---

## The gap (what's out there today)

We researched the landscape (mid-2026). The most popular self-hostable Telegram
AI bots are loved but **dated single-provider wrappers** — which is precisely the
opening this project fills:

| Project | Popularity | What it is | What it lacks (vs. this) |
|---|---|---|---|
| [father-bot/chatgpt_telegram_bot](https://github.com/father-bot/chatgpt_telegram_bot) | ~5.5k ★ | OpenAI-only ChatGPT bot | long-term memory, multi-provider, **monetization**, admin/roles |
| [n3d1117/chatgpt-telegram-bot](https://github.com/n3d1117/chatgpt-telegram-bot) | ~3.5k ★ | OpenAI-only, summarizes after ~15 msgs | persistent memory, Stars/tiers, admin dashboard |
| [Lifailon/openrouter-bot](https://github.com/Lifailon/openrouter-bot) | ~83 ★ (Go) | OpenRouter + local models, 1-line Docker | memory layer, monetization, Mini App, admin |
| [Memoh](https://github.com/memohai/Memoh) | multi-channel platform | self-hosted agents w/ long-term memory (Mem0/OpenViking) | Telegram-Stars monetization, priced tiers, Mini App focus |
| [donbarbos/telegram-bot-template](https://github.com/donbarbos/telegram-bot-template) | ~465 ★ | generic aiogram infra template | it's not an AI/memory product at all |

**Verified takeaways:** the two leading bots are OpenAI-only with **only
short-term, in-session memory** (n3d1117 resets after ~15 messages / 3h), have
**no built-in monetization** (donations or bring-your-own-key only), and **no
admin/role governance**. Long-term memory + Stars monetization + an admin
dashboard is the combination nobody ships together. ([father-bot](https://github.com/father-bot/chatgpt_telegram_bot),
[n3d1117](https://github.com/n3d1117/chatgpt-telegram-bot))

---

## 1. Indie hacker shipping a monetizable AI product this weekend 🚀

**Who:** a solo builder who wants a niche AI bot they can actually charge for —
without building billing, memory, and admin from scratch.

**The alternative today:** fork an OpenAI-only bot and bolt on Stripe, a memory
store, and an admin panel yourself — weeks of plumbing. Or pay a no-code builder
like **BotPenguin** ($29/mo mid-tier, $99/mo for multi-model + voice) and not own
your code or data. ([BotPenguin pricing](https://botpenguin.com/pricing))

**With this:** set one `SYSTEM_PROMPT`, run the installer, and you have memory +
**Telegram Stars** checkout + tiers + a dashboard on day one. Free OpenRouter
models mean your inference cost **starts at $0**, so you can validate before you
spend.

**Headline features:** editable persona · free-model rotation · GetMem memory ·
Mini App · Stars upgrade tiers.

---

## 2. Coach / creator monetizing expertise (the "memory moat") 💼

**Who:** a language teacher, nutritionist, trainer, or finance coach selling a
paid AI assistant trained on *their* method.

**Why memory is the moat:** the #1 missing feature in popular bots is
**persistent per-user memory** — they forget you between sessions. Coaching only
feels real if the assistant remembers the client's goals, history, and past
advice. That's the built-in headline here (via GetMem), not an add-on.

**Monetization that fits:** price your **Premium tier** in Telegram Stars, set
the daily limits, and manage clients from the dashboard (grant access, override
limits, ban abusers). Per-user **roles** let each client tune the assistant
("be strict", "explain like a beginner"). Memory-as-a-service vendors like
**Mem0** charge $19–$249/mo for the memory layer *alone*
([Mem0 pricing](https://mem0.ai/pricing)) — here it's part of the stack you own.

**Headline features:** long-term memory · custom priced tiers · per-user roles ·
admin user management · Stars.

---

## 3. Community / channel owner adding an AI perk 👥

**Who:** the admin of a Telegram group, channel, or paid community.

**The alternative today:** existing bots have **no daily limits and no tiers**,
so you can't safely open an AI bot to a crowd or reward supporters.

**With this:** everyone gets a **free daily quota**; supporters unlock a
**premium** plan (higher limits, better models) paid in Stars — which keeps the
money and the audience inside Telegram. Voice messages lower the barrier; admin
**ban/freeze** and per-user limit overrides keep abuse and cost in check. Stars
is increasingly the default for in-Telegram monetization in 2026.
([Telegram Stars guide](https://grambase.ai/blog/telegram-stars-guide-2026))

**Headline features:** free vs premium daily limits · voice · admin ban/freeze +
limit overrides · usage dashboard.

---

## 4. Developer template for memory-first AI agents 🛠️

**Who:** an engineer who wants a clean, modern reference — not a 200-line script
or a generic infra template with no AI in it (like the popular
[donbarbos template](https://github.com/donbarbos/telegram-bot-template), 465★).

**Why this:** the backend is **ports & adapters + a DI container** — the core
depends on interfaces (`LLMProvider`, `MemoryStore`, `Transcriber`), so swapping
OpenRouter for OpenAI/Anthropic/local, or the voice service, is a one-line
change. It's a working showcase of the GetMem SDK, OpenRouter multi-model
fallback, the official OpenAI/Anthropic SDKs, async SQLAlchemy + Alembic,
FastAPI + a Next.js Mini App, Docker/uv — wired together and tested. Fork it and
add your own tools, providers, or channels.

**Headline features:** the whole architecture — adapters, model router, config
store, migrations, Mini App API, three deploy modes (local / Caddy / Dokploy).

---

## 5. Self-hosted assistant for a team or SMB 🏢

**Who:** a team that wants a private AI helper (internal FAQ, onboarding buddy,
support draft-writer) **on their own server**, not a third-party SaaS.

**With this:** the whole stack runs in Docker on one box (Postgres + bot + API +
Mini App), so **your data stays with you** — and with **Ollama/local models** you
can run with *no external API at all*. Memory personalizes per employee; admins
control access and limits; the bundled Caddy/Dokploy setups give you a real
domain with automatic HTTPS. Point `SYSTEM_PROMPT` at your policies and you have
a private assistant in an afternoon.

**Headline features:** fully self-hosted Docker stack · per-user access & limits ·
memory · admin panel · auto-HTTPS deploy.

---

## How to think about monetization

AI products in 2026 converge on three charge metrics — **consumption** (per
message/credit), **workflow** (per task), and **outcome** (per result, e.g.
Intercom Fin's $0.99/resolution). ([BVP AI pricing playbook](https://www.bvp.com/atlas/the-ai-pricing-and-monetization-playbook))
This project maps cleanly to **consumption**: free daily quota → priced tiers in
Telegram Stars, all admin-configurable. Anchors to price against: BotPenguin
($0 / $29 / $99) and Mem0 ($0 / $19 / $79 / $249).

## Why this vs. the alternatives

| You want… | OpenAI-only OSS bots | No-code builders | Memory APIs | **This project** |
|---|:--:|:--:|:--:|:--:|
| Self-host & own your code/data | ✅ | ❌ | ❌ | ✅ |
| Long-term per-user memory | ❌ | partial | ✅ (only memory) | ✅ |
| Multiple providers + free models | ❌ | top tier only | — | ✅ |
| Built-in monetization (Stars/tiers) | ❌ | ✅ (paid SaaS) | ❌ | ✅ |
| Admin dashboard (ban/limit/grant) | ❌ | ✅ | ❌ | ✅ |
| One-command deploy | partial | n/a | n/a | ✅ |

---

**Try the live demo:** [@getmem_recall_bot](https://t.me/getmem_recall_bot)
**Run your own in one command:** see the [README](../README.md#-install-in-one-command).

<sub>Market figures verified mid-2026 from primary sources (GitHub, vendor
pricing pages); star counts and pricing drift over time. GetMem's own pricing is
not stated here as it was not independently verified.</sub>
