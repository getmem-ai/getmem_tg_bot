"""Inline keyboard builders."""

from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from . import texts

# Callback data prefixes.
CB_MODEL = "model"          # model:<name>  | model:__auto__
CB_UPGRADE = "upgrade"      # upgrade:buy
CB_FORGET = "forget"        # forget:yes | forget:no

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
