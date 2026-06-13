"""Mutable runtime state that admins can flip without a redeploy.

Settings (from the environment) are frozen and define the *defaults*. This small
object holds the live overrides an operator can toggle from the bot at runtime —
e.g. turn voice off, or disable a model that's misbehaving. It lives in the DI
container and is shared (by reference) with the handlers and the chat service.

State is in-memory and resets on restart, falling back to the env defaults —
which is the intended behaviour for quick operational toggles.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..config import Settings


@dataclass
class RuntimeState:
    voice_enabled: bool
    # Models an admin has temporarily taken out of rotation.
    disabled_models: set[str] = field(default_factory=set)

    @classmethod
    def from_settings(cls, settings: Settings) -> "RuntimeState":
        return cls(voice_enabled=settings.enable_voice)

    def toggle_voice(self) -> bool:
        self.voice_enabled = not self.voice_enabled
        return self.voice_enabled

    def toggle_model(self, model: str) -> bool:
        """Flip a model's enabled state. Returns True if now enabled."""
        if model in self.disabled_models:
            self.disabled_models.discard(model)
            return True
        self.disabled_models.add(model)
        return False

    def filter_models(self, models: list[str]) -> list[str]:
        return [m for m in models if m not in self.disabled_models]
