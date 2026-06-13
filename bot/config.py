"""Application configuration loaded from environment variables.

Everything the bot needs to run is read once here, validated, and exposed as a
frozen :class:`Settings` dataclass. Keep secrets in ``.env`` (see
``.env.example``) — never commit them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# ``python-dotenv`` is optional at runtime (Docker injects real env vars), but
# loading a local .env makes development painless.
try:  # pragma: no cover - trivial import guard
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _split(value: str | None) -> list[str]:
    """Parse a comma/newline separated env value into a clean list."""
    if not value:
        return []
    raw = value.replace("\n", ",")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


# Sensible free-tier defaults. Every one of these is a ``:free`` OpenRouter
# model at the time of writing; the bot rotates through them on failure so a
# single model being rate-limited or unavailable never takes the bot down.
DEFAULT_FREE_MODELS = [
    "deepseek/deepseek-chat-v3-0324:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
]

# Premium models unlocked after upgrading. Paid; only offered to premium users.
DEFAULT_PREMIUM_MODELS = [
    "anthropic/claude-sonnet-4-6",
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
]


@dataclass(frozen=True)
class Settings:
    # -- Telegram --------------------------------------------------------
    bot_token: str

    # -- OpenRouter ------------------------------------------------------
    openrouter_api_key: str
    openrouter_base_url: str
    free_models: list[str]
    premium_models: list[str]
    request_timeout: float
    app_url: str
    app_name: str

    # -- GetMem memory ---------------------------------------------------
    getmem_api_key: str
    getmem_base_url: str | None
    memory_token_budget: int

    # -- Limits ----------------------------------------------------------
    free_daily_limit: int
    premium_daily_limit: int

    # -- Payments (Telegram Stars) --------------------------------------
    premium_price_stars: int
    premium_period_days: int

    # -- Behaviour -------------------------------------------------------
    system_prompt: str
    max_history_turns: int
    db_path: str

    # -- Webhook (optional; long polling is used when WEBHOOK_URL is empty) --
    webhook_url: str
    webhook_path: str
    webhook_secret: str
    web_host: str
    web_port: int

    admin_ids: list[int] = field(default_factory=list)

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_url)

    @property
    def memory_enabled(self) -> bool:
        return bool(self.getmem_api_key)


DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant with long-term memory of the user. "
    "Use the provided memory context to personalise your answers and stay "
    "consistent across conversations. If the context is empty, just answer "
    "normally. Reply in the same language the user writes in. Be concise."
)


def load_settings() -> Settings:
    """Read, validate and return the application settings."""
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Create a bot with @BotFather and put the "
            "token in your .env file (see .env.example)."
        )

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not openrouter_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Get a free key at "
            "https://openrouter.ai/keys and add it to your .env file."
        )

    free_models = _split(os.getenv("FREE_MODELS")) or list(DEFAULT_FREE_MODELS)
    premium_models = _split(os.getenv("PREMIUM_MODELS")) or list(
        DEFAULT_PREMIUM_MODELS
    )

    admin_ids = []
    for chunk in _split(os.getenv("ADMIN_IDS")):
        try:
            admin_ids.append(int(chunk))
        except ValueError:
            continue

    db_path = os.getenv("DB_PATH", "data/bot.db").strip() or "data/bot.db"
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    return Settings(
        bot_token=bot_token,
        openrouter_api_key=openrouter_key,
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip(),
        free_models=free_models,
        premium_models=premium_models,
        request_timeout=float(os.getenv("REQUEST_TIMEOUT", "60")),
        app_url=os.getenv("APP_URL", "https://github.com/getmem-ai").strip(),
        app_name=os.getenv("APP_NAME", "GetMem Telegram Bot").strip(),
        getmem_api_key=os.getenv("GETMEM_API_KEY", "").strip(),
        getmem_base_url=os.getenv("GETMEM_BASE_URL", "").strip() or None,
        memory_token_budget=_int("MEMORY_TOKEN_BUDGET", 1500),
        free_daily_limit=_int("FREE_DAILY_LIMIT", 30),
        premium_daily_limit=_int("PREMIUM_DAILY_LIMIT", 500),
        premium_price_stars=_int("PREMIUM_PRICE_STARS", 250),
        premium_period_days=_int("PREMIUM_PERIOD_DAYS", 30),
        system_prompt=os.getenv("SYSTEM_PROMPT", "").strip()
        or DEFAULT_SYSTEM_PROMPT,
        max_history_turns=_int("MAX_HISTORY_TURNS", 10),
        db_path=db_path,
        webhook_url=os.getenv("WEBHOOK_URL", "").strip(),
        webhook_path=os.getenv("WEBHOOK_PATH", "/webhook").strip() or "/webhook",
        webhook_secret=os.getenv("WEBHOOK_SECRET", "").strip(),
        web_host=os.getenv("WEB_HOST", "0.0.0.0").strip() or "0.0.0.0",
        web_port=_int("WEB_PORT", 8080),
        admin_ids=admin_ids,
    )
