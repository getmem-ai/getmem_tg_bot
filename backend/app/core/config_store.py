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

    # -- welcome message (/start) ---------------------------------------

    async def welcome_message(self) -> str | None:
        """Custom /start message (or None to use the built-in default)."""
        stored = await self._get_str(repo.WELCOME_KEY)
        return stored if stored and stored.strip() else None

    async def set_welcome_message(self, text: str) -> None:
        """Set (or clear, with an empty string) the custom welcome message."""
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(session, repo.WELCOME_KEY, text.strip())

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

    async def generation_paused(self) -> bool:
        """Global kill-switch: when true, the bot stops generating replies."""
        return (await self._get_str(repo.GENERATION_PAUSED_KEY)) == "true"

    async def set_generation_paused(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.GENERATION_PAUSED_KEY, "true" if on else "false"
                )

    async def max_tokens(self) -> int:
        """Cap on tokens per reply (0 = provider default / unlimited)."""
        stored = await self._get_str(repo.MAX_TOKENS_KEY)
        try:
            return max(0, int(stored)) if stored else 0
        except ValueError:
            return 0

    async def set_max_tokens(self, value: int) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.MAX_TOKENS_KEY, str(max(0, value))
                )

    async def streaming_enabled(self) -> bool:
        """Stream replies token-by-token (default: enabled)."""
        stored = await self._get_str(repo.STREAMING_ENABLED_KEY)
        if stored is None:
            return True
        return stored == "true"

    async def set_streaming_enabled(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.STREAMING_ENABLED_KEY, "true" if on else "false"
                )

    async def onboarded(self) -> bool:
        """Whether the operator finished the first-run setup wizard."""
        return (await self._get_str(repo.ONBOARDED_KEY)) == "true"

    async def set_onboarded(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.ONBOARDED_KEY, "true" if on else "false"
                )

    # -- vision (image understanding) -----------------------------------

    async def vision_enabled(self) -> bool:
        """Whether the bot understands photos (default: disabled)."""
        return (await self._get_str(repo.VISION_ENABLED_KEY)) == "true"

    async def set_vision_enabled(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.VISION_ENABLED_KEY, "true" if on else "false"
                )

    async def vision_model(self) -> ModelSpec:
        """The model used for image messages. Must be a vision-capable model."""
        data = await self._get_json(repo.VISION_MODEL_KEY)
        if isinstance(data, dict) and data.get("id"):
            return ModelSpec(str(data.get("provider", "openrouter")), str(data["id"]))
        return ModelSpec("openrouter", "google/gemma-4-31b-it:free")

    async def set_vision_model(self, provider: str, model_id: str) -> None:
        await self._set_json(
            repo.VISION_MODEL_KEY, {"provider": provider, "id": model_id}
        )

    async def vision_premium_only(self) -> bool:
        """If true (default), only paid-tier users can send photos."""
        stored = await self._get_str(repo.VISION_PREMIUM_ONLY_KEY)
        return stored != "false"

    async def set_vision_premium_only(self, on: bool) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.VISION_PREMIUM_ONLY_KEY, "true" if on else "false"
                )

    # -- branding (white-label header) ----------------------------------

    async def brand_name(self) -> str:
        return (await self._get_str(repo.BRAND_NAME_KEY)) or "GetMem"

    async def brand_tagline(self) -> str:
        stored = await self._get_str(repo.BRAND_TAGLINE_KEY)
        return stored if stored is not None else "Memory-first assistant"

    async def set_brand(self, name: str, tagline: str) -> None:
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(session, repo.BRAND_NAME_KEY, name.strip())
                await repo.set_setting(
                    session, repo.BRAND_TAGLINE_KEY, tagline.strip()
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

    async def top_model_for_tier(self, tier: TierConfig) -> str | None:
        """The flagship model of a tier: the first model that is neither
        disabled nor on an unconfigured provider. Used to auto-select the best
        model for a user the moment they gain premium. Falls back to the tier's
        first model, or ``None`` for an empty tier."""
        disabled = await self.disabled_models()
        providers = await self.providers()
        for m in tier.models:
            if m.id in disabled:
                continue
            p = providers.get(m.provider)
            if p is not None and p.usable:
                return m.id
        return tier.models[0].id if tier.models else None

    # -- config export / import / template apply -------------------------

    CONFIG_VERSION = 1

    async def export_config(self) -> dict[str, object]:
        """Serialise the full editable config as a portable dict.

        Provider **API keys are deliberately excluded** — only name/enabled/
        models travel, matching the masked-key contract elsewhere.
        """
        providers = await self.providers()
        tiers = await self.tiers()
        vm = await self.vision_model()
        return {
            "version": self.CONFIG_VERSION,
            "system_prompt": await self.system_prompt(),
            "welcome_message": await self.welcome_message() or "",
            "brand": {
                "name": await self.brand_name(),
                "tagline": await self.brand_tagline(),
            },
            "max_tokens": await self.max_tokens(),
            "voice_enabled": await self.voice_enabled(),
            "vision_enabled": await self.vision_enabled(),
            "vision_premium_only": await self.vision_premium_only(),
            "vision_model": {"provider": vm.provider, "id": vm.id},
            "user_roles_enabled": await self.user_roles_enabled(),
            "streaming_enabled": await self.streaming_enabled(),
            "disabled_models": sorted(await self.disabled_models()),
            "providers": {
                name: {"enabled": p.enabled, "models": list(p.models)}
                for name, p in providers.items()
            },
            "tiers": [
                {
                    "key": t.key,
                    "name": t.name,
                    "daily_limit": t.daily_limit,
                    "price_stars": t.price_stars,
                    "period_days": t.period_days,
                    "models": [{"provider": m.provider, "id": m.id} for m in t.models],
                }
                for t in tiers.values()
            ],
        }

    async def apply_config(self, cfg: dict[str, object]) -> dict[str, list[str]]:
        """Apply a normalised config dict (from a template or an import).

        Tier model packages are inherited from the current config when a tier
        omits ``models`` (so templates never ship dead model slugs). Returns a
        summary of what was applied and what the operator still needs to do.
        """
        applied: list[str] = []
        todo: list[str] = []

        sp = cfg.get("system_prompt")
        if isinstance(sp, str) and sp.strip():
            await self.set_system_prompt(sp)
            applied.append("system prompt")
        if isinstance(cfg.get("welcome_message"), str):
            await self.set_welcome_message(cfg["welcome_message"])  # type: ignore[arg-type]
            applied.append("welcome message")
        brand = cfg.get("brand")
        if isinstance(brand, dict) and brand.get("name"):
            await self.set_brand(str(brand.get("name", "")), str(brand.get("tagline", "")))
            applied.append("branding")
        if "max_tokens" in cfg:
            try:
                await self.set_max_tokens(int(cfg["max_tokens"]))  # type: ignore[arg-type]
                applied.append("max tokens")
            except (TypeError, ValueError):
                pass

        toggles: list[tuple[str, object, str]] = [
            ("voice_enabled", self.set_voice_enabled, "voice"),
            ("vision_enabled", self.set_vision_enabled, "vision"),
            ("vision_premium_only", self.set_vision_premium_only, "vision premium-only"),
            ("user_roles_enabled", self.set_user_roles_enabled, "personal roles"),
            ("streaming_enabled", self.set_streaming_enabled, "streaming"),
        ]
        for key, setter, label in toggles:
            if isinstance(cfg.get(key), bool):
                await setter(cfg[key])  # type: ignore[operator]
                applied.append(label)

        vm = cfg.get("vision_model")
        if isinstance(vm, dict) and vm.get("id"):
            await self.set_vision_model(
                str(vm.get("provider", "openrouter")), str(vm["id"])
            )
            applied.append("vision model")
        if isinstance(cfg.get("disabled_models"), list):
            await self.set_disabled_models([str(m) for m in cfg["disabled_models"]])  # type: ignore[union-attr]

        provs = cfg.get("providers")
        if isinstance(provs, dict):
            current = await self.providers()
            for name, p in provs.items():
                if name not in current or not isinstance(p, dict):
                    continue
                try:
                    await self.set_provider(
                        name,
                        enabled=bool(p["enabled"]) if "enabled" in p else None,
                        models=(
                            [str(m) for m in p["models"]]
                            if isinstance(p.get("models"), list)
                            else None
                        ),
                    )
                except ValueError:
                    continue
            for name, prov in (await self.providers()).items():
                if prov.enabled and prov.requires_key and not prov.api_key:
                    todo.append(f"add an API key for {name}")

        tiers = cfg.get("tiers")
        if isinstance(tiers, list):
            current_tiers = await self.tiers()
            fallback = [
                {"provider": m.provider, "id": m.id}
                for m in self._default_tiers()["premium"].models
            ]
            out: list[dict[str, object]] = []
            for t in tiers:
                if not isinstance(t, dict) or not t.get("key"):
                    continue
                key = str(t["key"])
                models = t.get("models")
                if not isinstance(models, list) or not models:
                    cur = current_tiers.get(key)
                    if cur is not None:
                        models = [{"provider": m.provider, "id": m.id} for m in cur.models]
                    elif key == "free":
                        models = [
                            {"provider": m.provider, "id": m.id}
                            for m in self._default_free().models
                        ]
                    else:
                        models = fallback
                out.append({**t, "models": models})
            if out:
                await self.set_tiers(out)
                applied.append("tiers & limits")

        return {"applied": applied, "todo": todo}


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
