"""GetMem Telegram Bot — a memory-first chat bot + Mini App.

A well-structured monorepo backend: an aiogram v3 bot that chats through free
OpenRouter models and remembers its users via the GetMem memory service, plus a
FastAPI service powering a Telegram Mini App dashboard. Postgres is the
operational store; long-term memory lives in GetMem.
"""

from __future__ import annotations

__version__ = "0.2.0"
