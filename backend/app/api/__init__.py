"""FastAPI backend powering the Telegram Mini App dashboard."""

from __future__ import annotations

from .app import create_app

__all__ = ["create_app"]
