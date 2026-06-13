"""Slash-command handlers: /start, /help, /me, /model, /reset, /forget, /stats."""

from __future__ import annotations

from datetime import datetime, timezone

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from .. import keyboards, texts
from ..config import Settings
from ..limits import daily_limit, models_for
from ..memory import Memory
from ..storage import Storage

router = Router(name="commands")


@router.message(Command("start"))
async def cmd_start(message: Message, settings: Settings, storage: Storage) -> None:
    if message.from_user is None:
        return
    await storage.get_or_create_user(message.from_user.id)
    name = message.from_user.first_name or "there"
    await message.answer(texts.start(name, settings.memory_enabled))


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP, disable_web_page_preview=True)


@router.message(Command("me"))
async def cmd_me(message: Message, settings: Settings, storage: Storage) -> None:
    if message.from_user is None:
        return
    user = await storage.get_or_create_user(message.from_user.id)
    limit = daily_limit(settings, user)
    remaining = await storage.remaining_today(message.from_user.id, limit)
    used = limit - remaining
    model = user.model or "🔄 auto"
    premium_until = None
    if user.is_premium and user.premium_until:
        premium_until = datetime.fromtimestamp(
            user.premium_until, tz=timezone.utc
        ).strftime("%Y-%m-%d")
    await message.answer(
        texts.me(
            tier="premium" if user.is_premium else "free",
            used=used,
            limit=limit,
            model=model,
            premium_until=premium_until,
        )
    )


@router.message(Command("model"))
async def cmd_model(message: Message, settings: Settings, storage: Storage) -> None:
    if message.from_user is None:
        return
    user = await storage.get_or_create_user(message.from_user.id)
    text = (
        texts.MODEL_PICK_PREMIUM if user.is_premium else texts.MODEL_PICK_FREE
    )
    await message.answer(
        text,
        reply_markup=keyboards.model_keyboard(
            settings.free_models,
            settings.premium_models,
            is_premium=user.is_premium,
            current=user.model,
        ),
    )


@router.callback_query(F.data.startswith(f"{keyboards.CB_MODEL}:"))
async def on_model_pick(
    callback: CallbackQuery, settings: Settings, storage: Storage
) -> None:
    if callback.from_user is None or callback.data is None:
        return
    value = callback.data.split(":", 1)[1]
    user = await storage.get_or_create_user(callback.from_user.id)

    if value == keyboards.AUTO_VALUE:
        await storage.set_model(user.user_id, None)
        await callback.message.edit_text(texts.MODEL_SET_AUTO)
        await callback.answer()
        return

    allowed = models_for(settings, user)
    is_premium_model = value in settings.premium_models
    if is_premium_model and not user.is_premium:
        await callback.answer(texts.model_locked().replace("⭐", "").strip(), show_alert=True)
        return
    if value not in allowed:
        await callback.answer("Unknown model.", show_alert=True)
        return

    await storage.set_model(user.user_id, value)
    await callback.message.edit_text(texts.model_set(value))
    await callback.answer()


@router.message(Command("reset"))
async def cmd_reset(message: Message, storage: Storage) -> None:
    if message.from_user is None:
        return
    await storage.clear_history(message.from_user.id)
    await message.answer(texts.RESET_DONE)


@router.message(Command("forget"))
async def cmd_forget(message: Message) -> None:
    await message.answer(
        texts.FORGET_PROMPT, reply_markup=keyboards.confirm_forget_keyboard()
    )


@router.callback_query(F.data.startswith(f"{keyboards.CB_FORGET}:"))
async def on_forget(
    callback: CallbackQuery, memory: Memory, storage: Storage
) -> None:
    if callback.from_user is None or callback.data is None:
        return
    choice = callback.data.split(":", 1)[1]
    if choice == "no":
        await callback.message.edit_text(texts.FORGET_CANCEL)
        await callback.answer()
        return

    tg_id = callback.from_user.id
    count = await memory.forget(tg_id)
    await storage.clear_history(tg_id)
    await callback.message.edit_text(texts.forget_done(count))
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message, settings: Settings, storage: Storage) -> None:
    """Admin-only quick stats. Silently ignored for non-admins."""
    if message.from_user is None or message.from_user.id not in settings.admin_ids:
        return
    s = await storage.stats()
    await message.answer(
        "<b>📊 Stats</b>\n"
        f"Users: {s['users']}\n"
        f"Premium: {s['premium']}\n"
        f"Messages today: {s['messages_today']}\n"
        f"Payments: {s['payments']}"
    )
