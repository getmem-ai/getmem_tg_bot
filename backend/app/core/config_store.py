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
    kind: str  # openrouter | openai | anthropic
    enabled: bool
    is_default: bool
    api_key: str
    models: list[str] = field(default_factory=list)
    note: str | None = None

    @property
    def has_key(self) -> bool:
        return bool(self.api_key)


@dataclass
class TierConfig:
    key: str
    name: str
    daily_limit: int
    models: list[ModelSpec] = field(default_factory=list)


# Sensible direct-provider model defaults (admin can edit).
_DEFAULT_OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini"]
_DEFAULT_ANTHROPIC_MODELS = ["claude-sonnet-4-6", "claude-haiku-4-5-20251001"]


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

    async def disabled_models(self) -> set[str]:
        data = await self._get_json(repo.DISABLED_MODELS_KEY)
        return set(data) if isinstance(data, list) else set()

    async def set_disabled_models(self, models: list[str]) -> None:
        await self._set_json(repo.DISABLED_MODELS_KEY, sorted(set(models)))

    # -- providers -------------------------------------------------------

    async def providers(self) -> dict[str, Provider]:
        stored = await self._get_json(repo.PROVIDERS_KEY)
        stored = stored if isinstance(stored, dict) else {}

        def merged(name: str, kind: str, *, default_models: list[str]) -> Provider:
            s = stored.get(name, {}) if isinstance(stored.get(name), dict) else {}
            return Provider(
                name=name,
                kind=kind,
                enabled=bool(s.get("enabled", False)),
                is_default=False,
                api_key=str(s.get("api_key", "") or ""),
                models=list(s.get("models", default_models)),
            )

        # OpenRouter is the always-on default; its key comes from the env, and
        # its catalog defaults to the configured free+premium model slugs.
        or_stored = stored.get("openrouter", {}) if isinstance(stored.get("openrouter"), dict) else {}
        openrouter_models = list(
            or_stored.get(
                "models",
                _dedupe(self._settings.free_models + self._settings.premium_models),
            )
        )
        openrouter = Provider(
            name="openrouter",
            kind="openrouter",
            enabled=True,
            is_default=True,
            api_key=self._settings.openrouter_api_key,
            models=openrouter_models,
            note="Default provider — set OPENROUTER_API_KEY in env.",
        )

        openai = merged("openai", "openai", default_models=_DEFAULT_OPENAI_MODELS)
        openai.note = "Direct OpenAI access. Add your API key and pick models."
        anthropic = merged(
            "anthropic", "anthropic", default_models=_DEFAULT_ANTHROPIC_MODELS
        )
        anthropic.note = "Direct Anthropic access. Add your API key and pick models."

        return {"openrouter": openrouter, "openai": openai, "anthropic": anthropic}

    async def set_provider(
        self,
        name: str,
        *,
        enabled: bool | None = None,
        api_key: str | None = None,
        models: list[str] | None = None,
    ) -> Provider:
        if name not in {"openrouter", "openai", "anthropic"}:
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

    def _default_tiers(self) -> dict[str, TierConfig]:
        return {
            "free": TierConfig(
                key="free",
                name="Free",
                daily_limit=self._settings.free_daily_limit,
                models=[
                    ModelSpec("openrouter", m) for m in self._settings.free_models
                ],
            ),
            "premium": TierConfig(
                key="premium",
                name="Premium",
                daily_limit=self._settings.premium_daily_limit,
                models=[
                    ModelSpec("openrouter", m) for m in self._settings.premium_models
                ],
            ),
        }

    async def tiers(self) -> dict[str, TierConfig]:
        defaults = self._default_tiers()
        stored = await self._get_json(repo.TIERS_KEY)
        if not isinstance(stored, dict):
            return defaults
        out: dict[str, TierConfig] = {}
        for key, base in defaults.items():
            s = stored.get(key) if isinstance(stored.get(key), dict) else None
            if not s:
                out[key] = base
                continue
            models = [
                ModelSpec(m.get("provider", "openrouter"), m["id"])
                for m in s.get("models", [])
                if isinstance(m, dict) and m.get("id")
            ] or base.models
            out[key] = TierConfig(
                key=key,
                name=base.name,
                daily_limit=int(s.get("daily_limit", base.daily_limit)),
                models=models,
            )
        return out

    async def set_tiers(self, tiers: list[dict[str, object]]) -> dict[str, TierConfig]:
        # Merge with what's stored so a partial save (e.g. just "free" from the
        # Mini App) never wipes the other tier.
        existing = await self._get_json(repo.TIERS_KEY)
        stored: dict[str, object] = dict(existing) if isinstance(existing, dict) else {}
        for t in tiers:
            key = str(t.get("key", ""))
            if key not in {"free", "premium"}:
                continue
            models = [
                {"provider": m.get("provider", "openrouter"), "id": m["id"]}
                for m in t.get("models", [])  # type: ignore[union-attr]
                if isinstance(m, dict) and m.get("id")
            ]
            stored[key] = {
                "daily_limit": int(t.get("daily_limit", 0)),  # type: ignore[arg-type]
                "models": models,
            }
        await self._set_json(repo.TIERS_KEY, stored)
        return await self.tiers()

    async def tier_for(self, is_premium: bool) -> TierConfig:
        tiers = await self.tiers()
        return tiers["premium"] if is_premium else tiers["free"]


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            out.append(item)
    return out
