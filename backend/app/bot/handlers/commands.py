"""Slash-command handlers: /start, /help, /me, /model, /app, /reset, /forget, /stats."""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from ...config import Settings
from ...core import ConfigStore, MemoryStore
from ...db import Database, repo
from .. import keyboards, texts

router = Router(name="commands")


@router.message(Command("start"))
async def cmd_start(message: Message, settings: Settings, db: Database) -> None:
    tg = message.from_user
    if tg is None:
        return
    async with db.session() as session:
        await repo.get_or_create_user(
            session, tg.id, username=tg.username, first_name=tg.first_name
        )
    name = tg.first_name or "there"
    await message.answer(
        texts.start(name, settings.memory_enabled, settings.enable_voice),
        reply_markup=keyboards.app_keyboard(settings.miniapp_url),
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(texts.HELP, disable_web_page_preview=True)


@router.message(Command("app"))
async def cmd_app(message: Message, settings: Settings) -> None:
    if not settings.miniapp_url:
        await message.answer(texts.APP_DISABLED)
        return
    await message.answer(
        texts.APP_OPEN, reply_markup=keyboards.app_keyboard(settings.miniapp_url)
    )


@router.message(Command("me"))
async def cmd_me(
    message: Message, settings: Settings, db: Database, config: ConfigStore
) -> None:
    tg = message.from_user
    if tg is None:
        return
    async with db.session() as session:
        user = await repo.get_or_create_user(
            session, tg.id, username=tg.username, first_name=tg.first_name
        )
        used = await repo.used_today(session, tg.id)
        is_premium = user.is_premium
        model = user.preferred_model or "🔄 auto"
        premium_until = (
            user.premium_until.strftime("%Y-%m-%d")
            if is_premium and user.premium_until
            else None
        )
    limit = (await config.tier_for(is_premium)).daily_limit
    await message.answer(
        texts.me(
            tier="premium" if is_premium else "free",
            used=used,
            limit=limit,
            model=model,
            premium_until=premium_until,
        ),
        reply_markup=keyboards.app_keyboard(settings.miniapp_url),
    )


@router.message(Command("model"))
async def cmd_model(message: Message, db: Database, config: ConfigStore) -> None:
    tg = message.from_user
    if tg is None:
        return
    async with db.session() as session:
        user = await repo.get_or_create_user(session, tg.id)
        is_premium = user.is_premium
        current = user.preferred_model
    tier = await config.tier_for(is_premium)
    model_ids = [m.id for m in tier.models]
    await message.answer(
        texts.MODEL_PICK,
        reply_markup=keyboards.model_keyboard(model_ids, current=current),
    )


@router.callback_query(F.data.startswith(f"{keyboards.CB_MODEL}:"))
async def on_model_pick(
    callback: CallbackQuery, db: Database, config: ConfigStore
) -> None:
    if callback.from_user is None or callback.data is None:
        return
    value = callback.data.split(":", 1)[1]

    async with db.session() as session:
        user = await repo.get_or_create_user(session, callback.from_user.id)
        is_premium = user.is_premium

        if value == keyboards.AUTO_VALUE:
            await repo.set_preferred_model(session, callback.from_user.id, None)
            await _safe_edit(callback, texts.MODEL_SET_AUTO)
            await callback.answer()
            return

        tier = await config.tier_for(is_premium)
        if value not in {m.id for m in tier.models}:
            await callback.answer("That model isn't in your plan.", show_alert=True)
            return
        await repo.set_preferred_model(session, callback.from_user.id, value)

    await _safe_edit(callback, texts.model_set(value))
    await callback.answer()


@router.message(Command("reset"))
async def cmd_reset(message: Message, db: Database) -> None:
    if message.from_user is None:
        return
    async with db.session() as session:
        await repo.clear_history(session, message.from_user.id)
    await message.answer(texts.RESET_DONE)


@router.message(Command("forget"))
async def cmd_forget(message: Message) -> None:
    await message.answer(
        texts.FORGET_PROMPT, reply_markup=keyboards.confirm_forget_keyboard()
    )


@router.callback_query(F.data.startswith(f"{keyboards.CB_FORGET}:"))
async def on_forget(
    callback: CallbackQuery, memory: MemoryStore, db: Database
) -> None:
    if callback.from_user is None or callback.data is None:
        return
    choice = callback.data.split(":", 1)[1]
    if choice == "no":
        await _safe_edit(callback, texts.FORGET_CANCEL)
        await callback.answer()
        return

    tg_id = callback.from_user.id
    count = await memory.forget(tg_id)
    async with db.session() as session:
        await repo.clear_history(session, tg_id)
    await _safe_edit(callback, texts.forget_done(count))
    await callback.answer()


@router.message(Command("stats"))
async def cmd_stats(message: Message, settings: Settings, db: Database) -> None:
    """Admin-only quick stats. Silently ignored for non-admins."""
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return
    async with db.session() as session:
        s = await repo.global_stats(session)
    await message.answer(
        "<b>📊 Stats</b>\n"
        f"Users: {s['users']}\n"
        f"Premium: {s['premium']}\n"
        f"Messages today: {s['messages_today']}\n"
        f"Payments: {s['payments']}"
    )


async def _safe_edit(callback: CallbackQuery, text: str) -> None:
    if isinstance(callback.message, Message):
        await callback.message.edit_text(text)
