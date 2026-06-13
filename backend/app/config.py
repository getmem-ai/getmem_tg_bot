"""Application configuration loaded from environment variables.

One frozen :class:`Settings` object is built once and shared by the bot and the
API. Secrets live in ``.env`` (see ``.env.example``) — never commit them.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # pragma: no cover - dotenv is optional in containers
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _split(value: str | None) -> list[str]:
    if not value:
        return []
    raw = value.replace("\n", ",")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, "").strip() or default)
    except ValueError:
        return default


def _bool(name: str, default: bool) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on", "y"}


def _ids(value: str | None) -> list[int]:
    out: list[int] = []
    for chunk in _split(value):
        try:
            out.append(int(chunk))
        except ValueError:
            continue
    return out


# Free OpenRouter models, tried in order — the bot rotates to the next one when
# a model is rate-limited (429) or unavailable, so a single busy/retired model
# never takes it down. Free model availability changes often; verify the current
# list at https://openrouter.ai/models?max_price=0 and override via FREE_MODELS.
DEFAULT_FREE_MODELS = [
    "openai/gpt-oss-120b:free",
    "openai/gpt-oss-20b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
]

DEFAULT_PREMIUM_MODELS = [
    "anthropic/claude-sonnet-4-6",
    "openai/gpt-4o",
    "google/gemini-2.5-pro",
]

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful, friendly assistant with long-term memory of the user. "
    "Use the provided memory context to personalise your answers and stay "
    "consistent across conversations. If the context is empty, just answer "
    "normally. Reply in the same language the user writes in. Be concise."
)


def _database_url() -> str:
    """Resolve the async SQLAlchemy database URL.

    Prefer an explicit ``DATABASE_URL``; otherwise assemble one from the
    ``POSTGRES_*`` parts (matching the docker-compose service).
    """
    explicit = os.getenv("DATABASE_URL", "").strip()
    if explicit:
        # Normalise common sync URLs to the async driver.
        if explicit.startswith("postgresql://"):
            explicit = explicit.replace(
                "postgresql://", "postgresql+asyncpg://", 1
            )
        return explicit
    user = os.getenv("POSTGRES_USER", "getmem").strip()
    password = os.getenv("POSTGRES_PASSWORD", "getmem").strip()
    host = os.getenv("POSTGRES_HOST", "db").strip()
    port = os.getenv("POSTGRES_PORT", "5432").strip()
    name = os.getenv("POSTGRES_DB", "getmem_bot").strip()
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{name}"


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

    # -- Limits / premium ------------------------------------------------
    free_daily_limit: int
    premium_daily_limit: int
    premium_price_stars: int
    premium_period_days: int

    # -- Behaviour -------------------------------------------------------
    system_prompt: str
    max_history_turns: int

    # -- Voice (optional transcriber service) ----------------------------
    enable_voice: bool
    transcriber_url: str
    transcriber_timeout: float
    voice_max_duration: int

    # -- Database --------------------------------------------------------
    database_url: str

    # -- API / Mini App --------------------------------------------------
    api_host: str
    api_port: int
    cors_origins: list[str]
    miniapp_url: str
    init_data_max_age: int

    # -- Webhook (optional) ----------------------------------------------
    webhook_url: str
    webhook_path: str
    webhook_secret: str
    web_host: str
    web_port: int

    admin_ids: list[int] = field(default_factory=list)

    @property
    def memory_enabled(self) -> bool:
        return bool(self.getmem_api_key)

    @property
    def use_webhook(self) -> bool:
        return bool(self.webhook_url)

    def is_admin(self, user_id: int) -> bool:
        return user_id in self.admin_ids

    def daily_limit_for(self, is_premium: bool) -> int:
        return self.premium_daily_limit if is_premium else self.free_daily_limit


def load_settings(*, require_bot: bool = True, require_openrouter: bool = True) -> Settings:
    """Read, validate and return application settings.

    ``require_*`` let the API process start even if a bot-only secret is absent
    (and vice-versa), though normally both share one ``.env``.
    """
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if require_bot and not bot_token:
        raise RuntimeError(
            "BOT_TOKEN is not set. Create a bot with @BotFather and put the "
            "token in your .env file (see .env.example)."
        )

    openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if require_openrouter and not openrouter_key:
        raise RuntimeError(
            "OPENROUTER_API_KEY is not set. Get a free key at "
            "https://openrouter.ai/keys and add it to your .env file."
        )

    return Settings(
        bot_token=bot_token,
        openrouter_api_key=openrouter_key,
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ).strip(),
        free_models=_split(os.getenv("FREE_MODELS")) or list(DEFAULT_FREE_MODELS),
        premium_models=_split(os.getenv("PREMIUM_MODELS"))
        or list(DEFAULT_PREMIUM_MODELS),
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
        system_prompt=os.getenv("SYSTEM_PROMPT", "").strip() or DEFAULT_SYSTEM_PROMPT,
        max_history_turns=_int("MAX_HISTORY_TURNS", 10),
        enable_voice=_bool("ENABLE_VOICE", False),
        transcriber_url=os.getenv(
            "TRANSCRIBER_URL", "http://transcriber:8001"
        ).strip()
        or "http://transcriber:8001",
        transcriber_timeout=float(os.getenv("TRANSCRIBER_TIMEOUT", "120")),
        voice_max_duration=_int("VOICE_MAX_DURATION", 120),
        database_url=_database_url(),
        api_host=os.getenv("API_HOST", "0.0.0.0").strip() or "0.0.0.0",
        api_port=_int("API_PORT", 8000),
        cors_origins=_split(os.getenv("CORS_ORIGINS")) or ["*"],
        miniapp_url=os.getenv("MINIAPP_URL", "").strip(),
        init_data_max_age=_int("INIT_DATA_MAX_AGE", 86_400),
        webhook_url=os.getenv("WEBHOOK_URL", "").strip(),
        webhook_path=os.getenv("WEBHOOK_PATH", "/webhook").strip() or "/webhook",
        webhook_secret=os.getenv("WEBHOOK_SECRET", "").strip(),
        web_host=os.getenv("WEB_HOST", "0.0.0.0").strip() or "0.0.0.0",
        web_port=_int("WEB_PORT", 8080),
        admin_ids=_ids(os.getenv("ADMIN_IDS")),
    )
