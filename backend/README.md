# Backend — bot + Mini App API

The Python backend for the GetMem Telegram bot. One codebase, two entrypoints,
one DI container.

```
app/
├── config.py            Env-driven settings (frozen)
├── container.py         Composition root — wires adapters to ports
├── core/
│   ├── ports.py         Protocols: LLMProvider, MemoryStore, Transcriber
│   ├── service.py       ChatService (depends only on ports)
│   └── limits.py        Tier → quota & model pool
├── adapters/            Concrete implementations of the ports
│   ├── openrouter_llm.py    OpenRouter via the OpenAI SDK (native fallback)
│   ├── getmem_memory.py     Long-term memory via the getmem-ai SDK
│   └── http_transcriber.py  Calls the optional voice service
├── db/                  Async SQLAlchemy: base, models, repo
├── bot/                 aiogram v3: handlers, keyboards, texts, runner
├── api/                 FastAPI: routes, schemas, initData auth, deps
└── entrypoints/         bot.py / api.py
migrations/              Alembic (async)
vendor/getmem-ai/        Vendored memory SDK (path dependency)
```

## Architecture

The core depends on **ports** (`app/core/ports.py` — `Protocol` interfaces),
never on concrete vendor clients. Implementations live in `app/adapters/` and
are wired once in `app/container.py`. Swapping OpenRouter for another provider,
or the HTTP transcriber for an in-process one, is a one-line change in the
container — nothing else moves.

## Local development (uv)

```bash
cd backend
uv sync                       # creates a project-local .venv from uv.lock
uv run ruff check app
uv run pytest                 # unit tests (no DB/network needed)

# Run against a local Postgres (DATABASE_URL in your environment/.env):
uv run python -m app.entrypoints.bot
uv run python -m app.entrypoints.api
```

## Database migrations

```bash
uv run alembic upgrade head          # apply
uv run alembic revision --autogenerate -m "describe change"
```

In Docker, a one-shot `migrate` service runs `alembic upgrade head` before the
bot and API start.

## Entrypoints

| Command | Purpose |
|---|---|
| `python -m app.entrypoints.bot` | the Telegram bot (polling or webhook) |
| `python -m app.entrypoints.api` | the Mini App API (uvicorn) |
| `alembic upgrade head` | apply DB migrations |
