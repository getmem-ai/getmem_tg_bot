"""Database-backed, admin-editable configuration.

Everything an operator can change at runtime — the system prompt, voice on/off,
disabled models, the provider credentials/catalog and the per-tier model
packages — lives in the ``app_settings`` table as JSON and is read here. The
resolution rule is always **DB first, env/defaults as fallback**, so a fresh
install works from ``.env`` and every later tweak is stored in the DB and shared
across the bot and API processes (both read through this store).

Secrets (provider API keys) are stored here but never returned raw to clients;
the API layer masks them.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field

from ..config import Settings
from ..db import Database, repo


def model_label(model_id: str) -> str:
    """Human-friendly short label for a model id."""
    return model_id.split("/", 1)[-1].replace(":free", "")


@dataclass
class ModelSpec:
    provider: str
    id: str

    @property
    def label(self) -> str:
        return model_label(self.id)

    def as_dict(self) -> dict[str, str]:
        return {"provider": self.provider, "id": self.id, "label": self.label}


@dataclass
class Provider:
    name: str
    kind: str  # openrouter | openai | anthropic | groq | deepseek | mistral | gemini | ollama
    enabled: bool
    is_default: bool
    api_key: str
    base_url: str = ""
    models: list[str] = field(default_factory=list)
    note: str | None = None
    requires_key: bool = True  # ollama runs without an API key

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)

    @property
    def usable(self) -> bool:
        return self.enabled and (bool(self.api_key) or not self.requires_key)


@dataclass
class TierConfig:
    key: str
    name: str
    daily_limit: int
    price_stars: int = 0  # 0 = free (not purchasable)
    period_days: int = 30  # billing period for a paid tier
    models: list[ModelSpec] = field(default_factory=list)

    @property
    def is_paid(self) -> bool:
        return self.price_stars > 0 and self.key != "free"


# Direct (non-OpenRouter) providers. All except Anthropic speak the OpenAI
# Chat Completions API, so they share one adapter — only the base_url differs.
# `models` are sensible defaults the admin can edit in the dashboard.
# (name, kind, base_url, default_models, note, requires_key)
_DIRECT_PROVIDERS: list[tuple[str, str, str, list[str], str, bool]] = [
    (
        "openai", "openai", "https://api.openai.com/v1",
        ["gpt-4o", "gpt-4o-mini"],
        "Direct OpenAI. Add your API key and pick models.", True,
    ),
    (
        "anthropic", "anthropic", "",
        ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"],
        "Direct Anthropic (Claude). Add your API key and pick models.", True,
    ),
    (
        "groq", "groq", "https://api.groq.com/openai/v1",
        ["llama-3.3-70b-versatile", "openai/gpt-oss-120b"],
        "Groq — very fast inference, OpenAI-compatible.", True,
    ),
    (
        "deepseek", "deepseek", "https://api.deepseek.com/v1",
        ["deepseek-chat", "deepseek-reasoner"],
        "DeepSeek direct (OpenAI-compatible).", True,
    ),
    (
        "mistral", "mistral", "https://api.mistral.ai/v1",
        ["mistral-large-latest", "mistral-small-latest"],
        "Mistral direct (OpenAI-compatible).", True,
    ),
    (
        "gemini", "gemini",
        "https://generativelanguage.googleapis.com/v1beta/openai/",
        ["gemini-2.5-flash", "gemini-2.5-pro"],
        "Google Gemini via its OpenAI-compatible endpoint.", True,
    ),
    (
        "ollama", "ollama",
        os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434/v1"),
        ["llama3.1", "qwen2.5"],
        "Local models via Ollama — no API key required.", False,
    ),
]


class ConfigStore:
    """Typed accessors over the ``app_settings`` key-value table."""

    def __init__(self, db: Database | None, settings: Settings) -> None:
        self._db = db
        self._settings = settings

    # -- low-level helpers ----------------------------------------------

    async def _get_json(self, key: str) -> object | None:
        if self._db is None:
            return None
        async with self._db.session() as session:
            raw = await repo.get_setting(session, key)
        if not raw:
            return None
        try:
            return json.loads(raw)
        except (ValueError, TypeError):
            return None

    async def _set_json(self, key: str, value: object) -> None:
        if self._db is None:
            return
        async with self._db.session() as session:
            await repo.set_setting(session, key, json.dumps(value))

    # -- system prompt ---------------------------------------------------

    async def system_prompt(self) -> str:
        stored = await self._get_str(repo.SYSTEM_PROMPT_KEY)
        return stored or self._settings.system_prompt

    async def system_prompt_is_default(self) -> bool:
        return (await self._get_str(repo.SYSTEM_PROMPT_KEY)) is None

    async def set_system_prompt(self, prompt: str) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_system_prompt(session, prompt)

    async def _get_str(self, key: str) -> str | None:
        if self._db is None:
            return None
        async with self._db.session() as session:
            return await repo.get_setting(session, key)

    # -- runtime: voice + disabled models -------------------------------

    async def voice_enabled(self) -> bool:
        stored = await self._get_str(repo.VOICE_ENABLED_KEY)
        if stored is None:
            return self._settings.enable_voice
        return stored == "true"

    async def set_voice_enabled(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.VOICE_ENABLED_KEY, "true" if on else "false"
                )

    async def user_roles_enabled(self) -> bool:
        """Whether users may set a personal role (default: enabled)."""
        stored = await self._get_str(repo.USER_ROLES_KEY)
        if stored is None:
            return True
        return stored == "true"

    async def set_user_roles_enabled(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.USER_ROLES_KEY, "true" if on else "false"
                )

    async def disabled_models(self) -> set[str]:
        data = await self._get_json(repo.DISABLED_MODELS_KEY)
        return set(data) if isinstance(data, list) else set()

    async def set_disabled_models(self, models: list[str]) -> None:
        await self._set_json(repo.DISABLED_MODELS_KEY, sorted(set(models)))

    # -- providers -------------------------------------------------------

    async def providers(self) -> dict[str, Provider]:
        stored = await self._get_json(repo.PROVIDERS_KEY)
        stored = stored if isinstance(stored, dict) else {}

        def entry(name: str) -> dict:
            e = stored.get(name)
            return e if isinstance(e, dict) else {}

        # OpenRouter is the always-on default; its key comes from the env, and
        # its catalog defaults to the configured free+premium model slugs.
        oe = entry("openrouter")
        result: dict[str, Provider] = {
            "openrouter": Provider(
                name="openrouter",
                kind="openrouter",
                enabled=True,
                is_default=True,
                api_key=self._settings.openrouter_api_key,
                base_url=self._settings.openrouter_base_url,
                models=list(
                    oe.get(
                        "models",
                        _dedupe(
                            self._settings.free_models + self._settings.premium_models
                        ),
                    )
                ),
                note="Default provider — set OPENROUTER_API_KEY in env.",
                requires_key=True,
            )
        }
        for name, kind, base_url, default_models, note, requires_key in _DIRECT_PROVIDERS:
            s = entry(name)
            result[name] = Provider(
                name=name,
                kind=kind,
                enabled=bool(s.get("enabled", False)),
                is_default=False,
                api_key=str(s.get("api_key", "") or ""),
                base_url=base_url,
                models=list(s.get("models", default_models)),
                note=note,
                requires_key=requires_key,
            )
        return result

    async def set_provider(
        self,
        name: str,
        *,
        enabled: bool | None = None,
        api_key: str | None = None,
        models: list[str] | None = None,
    ) -> Provider:
        valid = {"openrouter"} | {p[0] for p in _DIRECT_PROVIDERS}
        if name not in valid:
            raise ValueError(f"Unknown provider: {name}")
        stored = await self._get_json(repo.PROVIDERS_KEY)
        stored = dict(stored) if isinstance(stored, dict) else {}
        entry = dict(stored.get(name, {})) if isinstance(stored.get(name), dict) else {}

        if enabled is not None:
            entry["enabled"] = bool(enabled)
        if models is not None:
            entry["models"] = [m.strip() for m in models if m.strip()]
        # api_key is write-only: only overwrite when a non-empty value is given.
        if api_key:
            entry["api_key"] = api_key.strip()

        stored[name] = entry
        await self._set_json(repo.PROVIDERS_KEY, stored)
        return (await self.providers())[name]

    # -- tiers -----------------------------------------------------------

    def _default_free(self) -> TierConfig:
        return TierConfig(
            key="free",
            name="Free",
            daily_limit=self._settings.free_daily_limit,
            price_stars=0,
            period_days=0,
            models=[ModelSpec("openrouter", m) for m in self._settings.free_models],
        )

    def _default_tiers(self) -> dict[str, TierConfig]:
        return {
            "free": self._default_free(),
            "premium": TierConfig(
                key="premium",
                name="Premium",
                daily_limit=self._settings.premium_daily_limit,
                price_stars=self._settings.premium_price_stars,
                period_days=self._settings.premium_period_days,
                models=[
                    ModelSpec("openrouter", m) for m in self._settings.premium_models
                ],
            ),
        }

    def _parse_tier(self, key: str, s: dict[str, object]) -> TierConfig:
        models = [
            ModelSpec(str(m.get("provider", "openrouter")), str(m["id"]))
            for m in s.get("models", [])  # type: ignore[union-attr]
            if isinstance(m, dict) and m.get("id")
        ]
        return TierConfig(
            key=key,
            name=str(s.get("name") or key.replace("_", " ").title()),
            daily_limit=int(s.get("daily_limit", 0)),  # type: ignore[arg-type]
            price_stars=int(s.get("price_stars", 0)),  # type: ignore[arg-type]
            period_days=int(s.get("period_days", self._settings.premium_period_days)),  # type: ignore[arg-type]
            models=models,
        )

    async def tiers(self) -> dict[str, TierConfig]:
        """All configured tiers (admin-defined; falls back to free+premium)."""
        stored = await self._get_json(repo.TIERS_KEY)
        if not isinstance(stored, dict) or not stored:
            return self._default_tiers()
        out: dict[str, TierConfig] = {}
        for key, s in stored.items():
            if isinstance(s, dict):
                out[str(key)] = self._parse_tier(str(key), s)
        # Free is always available, even if an admin omits it.
        out.setdefault("free", self._default_free())
        return out

    async def set_tiers(self, tiers: list[dict[str, object]]) -> dict[str, TierConfig]:
        """Replace the full tier set. A ``free`` tier is always kept."""
        stored: dict[str, object] = {}
        for t in tiers:
            key = _slug(str(t.get("key", "")))
            if not key:
                continue
            models = [
                {"provider": m.get("provider", "openrouter"), "id": m["id"]}
                for m in t.get("models", [])  # type: ignore[union-attr]
                if isinstance(m, dict) and m.get("id")
            ]
            stored[key] = {
                "name": str(t.get("name") or key.replace("_", " ").title()),
                "daily_limit": int(t.get("daily_limit", 0)),  # type: ignore[arg-type]
                "price_stars": 0 if key == "free" else int(t.get("price_stars", 0)),  # type: ignore[arg-type]
                "period_days": int(t.get("period_days", self._settings.premium_period_days)),  # type: ignore[arg-type]
                "models": models,
            }
        if "free" not in stored:
            f = self._default_free()
            stored["free"] = {
                "name": f.name,
                "daily_limit": f.daily_limit,
                "price_stars": 0,
                "period_days": 0,
                "models": [{"provider": m.provider, "id": m.id} for m in f.models],
            }
        await self._set_json(repo.TIERS_KEY, stored)
        return await self.tiers()

    async def paid_tiers(self) -> list[TierConfig]:
        """Purchasable tiers (price > 0), for the bot's /upgrade flow."""
        return [t for t in (await self.tiers()).values() if t.is_paid]

    async def tier_for_user(self, user: "object") -> TierConfig:
        """The user's effective tier: their paid tier if active, else free."""
        tiers = await self.tiers()
        key = getattr(user, "tier", "free")
        if getattr(user, "is_premium", False) and key in tiers and key != "free":
            return tiers[key]
        return tiers.get("free") or self._default_free()


def _slug(value: str) -> str:
    """Normalise a tier key: lowercase, alnum + underscores."""
    out = "".join(c if c.isalnum() else "_" for c in value.strip().lower())
    return "_".join(part for part in out.split("_") if part)


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
