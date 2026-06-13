"""Inline keyboard builders."""

from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import texts

# Callback data prefixes.
CB_MODEL = "model"          # model:<name>  | model:__auto__
CB_UPGRADE = "upgrade"      # upgrade:buy
CB_FORGET = "forget"        # forget:yes | forget:no
CB_ADMIN = "adm"            # adm:voice | adm:models | adm:back | adm:refresh
CB_ADMIN_MODEL = "admm"     # admm:<index>  (toggle model by index in the pool)

AUTO_VALUE = "__auto__"


def model_keyboard(
    free_models: list[str],
    premium_models: list[str],
    *,
    is_premium: bool,
    current: str | None,
) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()

    auto_label = texts.MODEL_AUTO + (" ✓" if current is None else "")
    kb.row(InlineKeyboardButton(text=auto_label, callback_data=f"{CB_MODEL}:{AUTO_VALUE}"))

    for model in free_models:
        mark = " ✓" if model == current else ""
        kb.row(
            InlineKeyboardButton(
                text=f"🆓 {_short(model)}{mark}",
                callback_data=f"{CB_MODEL}:{model}",
            )
        )

    for model in premium_models:
        mark = " ✓" if model == current else ""
        lock = "" if is_premium else " 🔒"
        kb.row(
            InlineKeyboardButton(
                text=f"⭐ {_short(model)}{mark}{lock}",
                callback_data=f"{CB_MODEL}:{model}",
            )
        )
    return kb.as_markup()


def upgrade_keyboard(price: int) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text=f"⭐ Pay {price} Stars", callback_data=f"{CB_UPGRADE}:buy"
        )
    )
    return kb.as_markup()


def app_keyboard(miniapp_url: str) -> InlineKeyboardMarkup | None:
    """A button that opens the Telegram Mini App, or None if not configured.

    Telegram only accepts ``web_app`` buttons over HTTPS, so we skip the button
    for non-HTTPS URLs (e.g. local dev) rather than send an invalid keyboard.
    """
    if not miniapp_url or not miniapp_url.startswith("https://"):
        return None
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text=texts.OPEN_APP_BUTTON, web_app=WebAppInfo(url=miniapp_url)
        )
    )
    return kb.as_markup()


def admin_panel_keyboard(*, voice_on: bool) -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(
            text=f"🎤 Voice: {'ON ✅' if voice_on else 'OFF 🚫'}",
            callback_data=f"{CB_ADMIN}:voice",
        )
    )
    kb.row(
        InlineKeyboardButton(text="🤖 Manage models", callback_data=f"{CB_ADMIN}:models")
    )
    kb.row(
        InlineKeyboardButton(text="🔄 Refresh", callback_data=f"{CB_ADMIN}:refresh")
    )
    return kb.as_markup()


def admin_models_keyboard(
    pool: list[str], disabled: set[str]
) -> InlineKeyboardMarkup:
    """One button per model (by index, to keep callback_data short)."""
    kb = InlineKeyboardBuilder()
    for idx, model in enumerate(pool):
        off = model in disabled
        kb.row(
            InlineKeyboardButton(
                text=f"{'🚫' if off else '✅'} {_short(model)}",
                callback_data=f"{CB_ADMIN_MODEL}:{idx}",
            )
        )
    kb.row(InlineKeyboardButton(text="⬅️ Back", callback_data=f"{CB_ADMIN}:back"))
    return kb.as_markup()


def confirm_forget_keyboard() -> InlineKeyboardMarkup:
    kb = InlineKeyboardBuilder()
    kb.row(
        InlineKeyboardButton(text="🗑️ Yes, erase", callback_data=f"{CB_FORGET}:yes"),
        InlineKeyboardButton(text="Cancel", callback_data=f"{CB_FORGET}:no"),
    )
    return kb.as_markup()


def _short(model: str) -> str:
    """Trim a provider/model:tag id to something readable on a button."""
    name = model.split("/", 1)[-1]
    return name.replace(":free", "")
