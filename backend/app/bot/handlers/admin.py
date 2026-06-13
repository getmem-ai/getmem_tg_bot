"""Admin handlers — live bot management for operators in ``ADMIN_IDS``.

From inside Telegram an admin can, without a redeploy:
  • toggle voice transcription on/off,
  • take a misbehaving model out of rotation (and put it back),
  • see live stats.

All handlers are gated by :meth:`Settings.is_admin`; non-admins are ignored.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from ...config import Settings
from ...core import RuntimeState
from ...db import Database, repo
from .. import keyboards, texts

router = Router(name="admin")


def _full_pool(settings: Settings) -> list[str]:
    """Stable index space for model-toggle callbacks (free + premium)."""
    return list(settings.free_models) + list(settings.premium_models)


async def _panel_text(settings: Settings, db: Database, runtime: RuntimeState) -> str:
    async with db.session() as session:
        stats = await repo.global_stats(session)
    return texts.admin_panel(
        voice_on=runtime.voice_enabled,
        disabled_models=len(runtime.disabled_models),
        stats=stats,
    )


@router.message(Command("admin"))
async def cmd_admin(
    message: Message, settings: Settings, db: Database, runtime: RuntimeState
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return  # silently ignore non-admins
    await message.answer(
        await _panel_text(settings, db, runtime),
        reply_markup=keyboards.admin_panel_keyboard(voice_on=runtime.voice_enabled),
    )


@router.message(Command("getprompt"))
async def cmd_getprompt(
    message: Message, settings: Settings, db: Database
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return
    async with db.session() as session:
        prompt = await repo.get_system_prompt(session, settings.system_prompt)
        is_default = (await repo.get_setting(session, repo.SYSTEM_PROMPT_KEY)) is None
    await message.answer(texts.admin_prompt_show(prompt, is_default))


@router.message(Command("setprompt"))
async def cmd_setprompt(
    message: Message, command: CommandObject, settings: Settings, db: Database
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return
    new_prompt = (command.args or "").strip()
    if not new_prompt:
        await message.answer(texts.ADMIN_SETPROMPT_USAGE)
        return
    async with db.session() as session:
        await repo.set_system_prompt(session, new_prompt)
    await message.answer(texts.admin_prompt_saved(new_prompt))


@router.callback_query(F.data.startswith(f"{keyboards.CB_ADMIN}:"))
async def on_admin_action(
    callback: CallbackQuery, settings: Settings, db: Database, runtime: RuntimeState
) -> None:
    if callback.from_user is None or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.ADMIN_ONLY, show_alert=True)
        return
    if callback.data is None or not isinstance(callback.message, Message):
        await callback.answer()
        return

    action = callback.data.split(":", 1)[1]

    if action == "voice":
        on = await runtime.toggle_voice()
        await callback.answer(texts.admin_voice_toggled(on))
        await callback.message.edit_text(
            await _panel_text(settings, db, runtime),
            reply_markup=keyboards.admin_panel_keyboard(voice_on=runtime.voice_enabled),
        )
    elif action in {"back", "refresh"}:
        await callback.answer()
        await callback.message.edit_text(
            await _panel_text(settings, db, runtime),
            reply_markup=keyboards.admin_panel_keyboard(voice_on=runtime.voice_enabled),
        )
    elif action == "models":
        await callback.answer()
        await callback.message.edit_text(
            texts.ADMIN_MODELS_TITLE,
            reply_markup=keyboards.admin_models_keyboard(
                _full_pool(settings), runtime.disabled_models
            ),
        )


@router.callback_query(F.data.startswith(f"{keyboards.CB_ADMIN_MODEL}:"))
async def on_admin_model_toggle(
    callback: CallbackQuery, settings: Settings, runtime: RuntimeState
) -> None:
    if callback.from_user is None or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.ADMIN_ONLY, show_alert=True)
        return
    if callback.data is None or not isinstance(callback.message, Message):
        await callback.answer()
        return

    pool = _full_pool(settings)
    try:
        idx = int(callback.data.split(":", 1)[1])
        model = pool[idx]
    except (ValueError, IndexError):
        await callback.answer("Unknown model.", show_alert=True)
        return

    enabled = await runtime.toggle_model(model)
    await callback.answer(texts.admin_model_toggled(model, enabled))
    await callback.message.edit_reply_markup(
        reply_markup=keyboards.admin_models_keyboard(pool, runtime.disabled_models)
    )
