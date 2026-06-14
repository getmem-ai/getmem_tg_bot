"""Starter bot templates — curated presets that configure the bot for a use case.

Each preset is a JSON file in ``backend/app/templates/*.json`` so non-developers
can add new ones without touching app code. A template is essentially a curated
*exported config*: persona, welcome message, branding, feature toggles and
tier limits/prices. Model packages are intentionally inherited from the
operator's current config on apply (so a preset never ships dead model slugs and
always works with whatever providers are configured).

Schema (all fields optional except ``key``/``name``)::

    {
      "key": "language-tutor",
      "name": "Language tutor",
      "emoji": "🗣️",
      "description": "Patient tutor that corrects and explains.",
      "system_prompt": "...",
      "welcome_message": "👋 Hi {name}! ...",
      "brand": {"name": "LinguaBot", "tagline": "Your pocket tutor"},
      "max_tokens": 0,
      "toggles": {"voice": true, "vision": false,
                   "vision_premium_only": true, "user_roles": true},
      "tiers": [
        {"key": "free", "name": "Free", "daily_limit": 20,
         "price_stars": 0, "period_days": 0},
        {"key": "premium", "name": "Premium", "daily_limit": 500,
         "price_stars": 200, "period_days": 30}
      ]
    }
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

_DIR = Path(__file__).resolve().parent.parent / "templates"


@lru_cache(maxsize=1)
def _load() -> dict[str, dict]:
    out: dict[str, dict] = {}
    if not _DIR.is_dir():
        return out
    for path in sorted(_DIR.glob("*.json")):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            continue
        if not isinstance(data, dict):
            continue
        key = str(data.get("key") or path.stem)
        data["key"] = key
        out[key] = data
    return out


def list_templates() -> list[dict]:
    """All templates, ordered by filename."""
    return list(_load().values())


def get_template(key: str) -> dict | None:
    return _load().get(key)


_TOGGLE_MAP = {
    "voice": "voice_enabled",
    "vision": "vision_enabled",
    "vision_premium_only": "vision_premium_only",
    "user_roles": "user_roles_enabled",
}


def template_to_config(tmpl: dict) -> dict:
    """Flatten a template into the normalised config shape ConfigStore.apply_config
    consumes (toggles → top-level *_enabled keys). Model packages are left to be
    inherited from the operator's current tiers."""
    cfg: dict = {}
    for k in ("system_prompt", "welcome_message", "brand", "max_tokens", "tiers"):
        if k in tmpl:
            cfg[k] = tmpl[k]
    toggles = tmpl.get("toggles") or {}
    for tkey, ckey in _TOGGLE_MAP.items():
        if tkey in toggles:
            cfg[ckey] = bool(toggles[tkey])
    return cfg
