"""Aggregate all feature routers into one for easy registration."""

from __future__ import annotations

from aiogram import Router

from . import admin, chat, commands, payments


def build_router() -> Router:
    root = Router(name="root")
    # Commands, admin and payments first so their filters win over the catch-all
    # chat handler that matches any non-slash text / voice.
    root.include_router(admin.router)
    root.include_router(commands.router)
    root.include_router(payments.router)
    root.include_router(chat.router)
    return root
