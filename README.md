<h1 align="center">🧠 GetMem Telegram Bot</h1>

<p align="center">
  A memory-first Telegram chat bot.<br>
  <b>aiogram v3</b> · free <b>OpenRouter</b> models with auto-fallback · long-term memory via <a href="https://getmem.ai"><b>GetMem</b></a>.
</p>

<p align="center">
  <img alt="Python" src="https://img.shields.io/badge/python-3.10%2B-blue">
  <img alt="aiogram" src="https://img.shields.io/badge/aiogram-3.x-2CA5E0">
  <img alt="License" src="https://img.shields.io/badge/license-MIT-green">
</p>

---

A Telegram bot that actually **remembers you**. Every conversation is ingested
into [GetMem](https://getmem.ai); before each reply the bot recalls a compact,
ranked context about you and personalises the answer. It runs on **free**
OpenRouter models (rotating through several so a single rate-limited model never
takes it down), enforces **per-user daily limits**, and can sell a **premium**
tier — higher limits + top models like Claude and GPT-4o — paid for with
**Telegram Stars**, no external payment provider required.

> The star of the show is **memory**. The bot is a thin, well-structured
> showcase of how easy it is to give an AI agent long-term memory with the
> GetMem SDK — drop in a key and your bot remembers its users forever.

## ✨ Features

- 🧠 **Long-term memory** — personalised replies via the GetMem SDK; `/forget` for GDPR erasure.
- 🔄 **Free models with auto-fallback** — rotates through a configurable pool; degrades gracefully.
- 🎚️ **Per-user daily limits** — separate free / premium quotas with a daily reset.
- ⭐ **Premium via Telegram Stars** — `/upgrade` unlocks premium models & higher limits. No Stripe, no provider token.
- 🧩 **Model picker** — `/model` lets users choose a model or leave it on auto.
- 🐳 **Docker-first** — `docker compose up` for polling; bundled **Caddy** config for a domain with **automatic HTTPS**.
- 🧪 **Tested & typed** — unit tests, `ruff`, clean modular architecture.

## 🚀 Quick start (local, long polling)

You need a **Telegram bot token** ([@BotFather](https://t.me/BotFather)) and a
free **OpenRouter API key** ([openrouter.ai/keys](https://openrouter.ai/keys)).
A **GetMem key** ([getmem.ai](https://getmem.ai)) is optional but it's the whole
point — without it the bot still chats, just without memory.

```bash
git clone https://github.com/getmem-ai/getmem_tg_bot.git && cd getmem_tg_bot
cp .env.example .env          # then fill in BOT_TOKEN, OPENROUTER_API_KEY, GETMEM_API_KEY
docker compose up -d --build  # done — message your bot
```

No Docker? Use a virtualenv:

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # fill it in
python -m bot
```

## ⚙️ Configuration

All configuration is via environment variables (or a `.env` file). The full,
commented list lives in [`.env.example`](.env.example). The essentials:

| Variable | Required | Default | Description |
|---|:---:|---|---|
| `BOT_TOKEN` | ✅ | — | Telegram bot token from @BotFather. |
| `OPENROUTER_API_KEY` | ✅ | — | OpenRouter key (free to create). |
| `GETMEM_API_KEY` | ⭐ | — | GetMem `gm_live_...` key. Empty = no memory. |
| `FREE_MODELS` | | 5 free models | Comma-separated pool, tried in order. |
| `PREMIUM_MODELS` | | Claude / GPT-4o / Gemini | Offered after `/upgrade`. |
| `FREE_DAILY_LIMIT` | | `30` | Messages/day for free users. |
| `PREMIUM_DAILY_LIMIT` | | `500` | Messages/day for premium users. |
| `PREMIUM_PRICE_STARS` | | `250` | Price of premium in Telegram Stars. |
| `PREMIUM_PERIOD_DAYS` | | `30` | Premium duration per purchase. |
| `SYSTEM_PROMPT` | | sensible default | The assistant's persona/instructions. |
| `ADMIN_IDS` | | — | Telegram IDs allowed to run `/stats`. |

## 💬 Commands

| Command | Description |
|---|---|
| `/start` | Intro |
| `/help` | What the bot can do |
| `/me` | Your plan, usage and remaining messages today |
| `/model` | Pick the AI model (or auto-rotate) |
| `/upgrade` | Unlock premium models & higher limits via Telegram Stars |
| `/reset` | Clear the short-term chat window |
| `/forget` | Erase **all** long-term memory about you |
| `/stats` | (admin) usage stats |

## 🧠 How memory works

The bot treats GetMem as its long-term brain, while a small local SQLite file
holds only operational state (quotas, the short rolling prompt window).

```
        ┌──────────── on each user message ─────────────┐
        │                                               │
  user text ──► memory.recall(query) ──► GetMem /get ──► ranked context
        │                                               │
        ▼                                               ▼
  recent history (SQLite) ─────────────► prompt ──► OpenRouter (model pool)
                                                        │
                                            assistant reply ──► user
                                                        │
        memory.remember(user, assistant) ──► GetMem /ingest  (background)
```

Each Telegram user maps to a stable GetMem `user_id` (`tg_<id>`), so memory is
isolated per user. Recall and ingest are **best-effort**: if memory is disabled
or the service hiccups, the bot keeps chatting without personalisation. See
[`bot/memory.py`](bot/memory.py) — it's a clean, ~120-line wrapper over the SDK
you can lift into your own project.

## 🏗️ Architecture

```
bot/
├── __main__.py      Entrypoint: wiring, polling/webhook runners
├── config.py        Env-driven settings (validated, frozen)
├── storage.py       Async SQLite: users, quotas, history, payments
├── memory.py        GetMem SDK wrapper  ← the core value
├── llm.py           OpenRouter client with model rotation/fallback
├── service.py       Orchestration: recall → prompt → generate → remember
├── limits.py        Tier → quota & model-pool resolution
├── keyboards.py     Inline keyboards
├── texts.py         All user-facing strings (easy i18n)
└── handlers/        Telegram handlers: chat, commands, payments
third_party/getmem-ai/   Vendored GetMem SDK (see below)
deploy/                  Production webhook + Caddy auto-HTTPS
tests/                   Unit tests (storage, limits, llm, splitting)
```

Each layer has one job and is independently testable; Telegram concerns
(handlers) are kept separate from AI concerns (`service`/`llm`/`memory`).

## 🐳 Deployment

- **Long polling (default):** no domain, no open ports, no TLS — just
  `docker compose up -d --build`. Best for a single server.
- **Webhook + custom domain + automatic HTTPS:** see
  [`deploy/README.md`](deploy/README.md). Bundled Caddy obtains and renews a
  Let's Encrypt certificate for your domain automatically — set `WEBHOOK_URL`
  and run the prod compose file.

## 📦 Memory SDK

This project uses the official **GetMem Python SDK** (`getmem-ai`). Until it's
published to PyPI it's **vendored** under [`third_party/getmem-ai`](third_party/getmem-ai)
so the bot builds out of the box. When the package is on PyPI, delete that
folder and the `[tool.uv.sources]` block in `pyproject.toml`, then depend on
`getmem-ai` directly — nothing else changes.

## 🧪 Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"     # or: pip install -r requirements.txt && pip install pytest pytest-asyncio respx ruff
pytest                       # run tests (no network needed)
ruff check bot/ tests/       # lint
```

## 📄 License

[MIT](LICENSE). Built to showcase [GetMem](https://getmem.ai) — long-term memory
for AI agents.
