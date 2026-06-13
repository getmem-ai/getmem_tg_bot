"""Runtime state that admins can flip live — persisted in the database.

Resolution order for every toggle is **database first, then the env default**:
on startup :meth:`load` reads the stored value; if nothing is stored yet it
falls back to the corresponding ``.env`` setting. Each change is written back to
the DB (the ``app_settings`` table), so it survives restarts and doesn't live in
``.env`` (which stays for first-run defaults only).

The in-memory copy is the fast path the hot loops read; the bot is the only
writer, and it persists on every change, so the two never diverge.
"""

from __future__ import annotations

import json

from ..config import Settings
from ..db import Database, repo


class RuntimeState:
    def __init__(self, db: Database | None, *, default_voice: bool) -> None:
        self._db = db
        self._default_voice = default_voice
        self.voice_enabled = default_voice
        self.disabled_models: set[str] = set()

    @classmethod
    def from_settings(
        cls, settings: Settings, db: Database | None = None
    ) -> "RuntimeState":
        return cls(db, default_voice=settings.enable_voice)

    async def load(self) -> None:
        """Hydrate from the DB (DB wins; else keep the env defaults)."""
        if self._db is None:
            return
        async with self._db.session() as session:
            voice = await repo.get_setting(session, repo.VOICE_ENABLED_KEY)
            if voice is not None:
                self.voice_enabled = voice == "true"
            disabled = await repo.get_setting(session, repo.DISABLED_MODELS_KEY)
            if disabled:
                try:
                    self.disabled_models = set(json.loads(disabled))
                except (ValueError, TypeError):
                    self.disabled_models = set()

    async def set_voice(self, on: bool) -> bool:
        self.voice_enabled = on
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session, repo.VOICE_ENABLED_KEY, "true" if on else "false"
                )
        return self.voice_enabled

    async def toggle_voice(self) -> bool:
        return await self.set_voice(not self.voice_enabled)

    async def toggle_model(self, model: str) -> bool:
        """Flip a model's enabled state and persist. Returns True if now enabled."""
        if model in self.disabled_models:
            self.disabled_models.discard(model)
            enabled = True
        else:
            self.disabled_models.add(model)
            enabled = False
        if self._db is not None:
            async with self._db.session() as session:
                await repo.set_setting(
                    session,
                    repo.DISABLED_MODELS_KEY,
                    json.dumps(sorted(self.disabled_models)),
                )
        return enabled

    def filter_models(self, models: list[str]) -> list[str]:
        return [m for m in models if m not in self.disabled_models]
