"""Admin handlers — live bot management for operators in ``ADMIN_IDS``.

From inside Telegram an admin can, without a redeploy:
  • toggle voice transcription on/off,
  • take a misbehaving model out of rotation (and put it back),
  • view/change the system prompt,
  • see live stats.

All state is read/written through :class:`~app.core.config_store.ConfigStore`
(DB-backed), so changes are shared with the Mini App and survive restarts. All
handlers are gated by :meth:`Settings.is_admin`; non-admins are ignored.
"""

from __future__ import annotations

from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.types import CallbackQuery, Message

from ...config import Settings
from ...core import ConfigStore
from ...db import Database, repo
from .. import keyboards, texts

router = Router(name="admin")


async def _all_models(config: ConfigStore) -> list[str]:
    """Every model id across all tiers — the admin's enable/disable space."""
    tiers = await config.tiers()
    seen: dict[str, None] = {}
    for tier in tiers.values():
        for m in tier.models:
            seen.setdefault(m.id, None)
    return list(seen)


async def _panel_text(db: Database, config: ConfigStore) -> str:
    async with db.session() as session:
        stats = await repo.global_stats(session)
    return texts.admin_panel(
        voice_on=await config.voice_enabled(),
        disabled_models=len(await config.disabled_models()),
        stats=stats,
    )


@router.message(Command("admin"))
async def cmd_admin(
    message: Message, settings: Settings, db: Database, config: ConfigStore
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return  # silently ignore non-admins
    await message.answer(
        await _panel_text(db, config),
        reply_markup=keyboards.admin_panel_keyboard(
            voice_on=await config.voice_enabled()
        ),
    )


@router.message(Command("getprompt"))
async def cmd_getprompt(
    message: Message, settings: Settings, config: ConfigStore
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return
    prompt = await config.system_prompt()
    is_default = await config.system_prompt_is_default()
    await message.answer(texts.admin_prompt_show(prompt, is_default))


@router.message(Command("setprompt"))
async def cmd_setprompt(
    message: Message, command: CommandObject, settings: Settings, config: ConfigStore
) -> None:
    if message.from_user is None or not settings.is_admin(message.from_user.id):
        return
    new_prompt = (command.args or "").strip()
    if not new_prompt:
        await message.answer(texts.ADMIN_SETPROMPT_USAGE)
        return
    await config.set_system_prompt(new_prompt)
    await message.answer(texts.admin_prompt_saved(new_prompt))


@router.callback_query(F.data.startswith(f"{keyboards.CB_ADMIN}:"))
async def on_admin_action(
    callback: CallbackQuery, settings: Settings, db: Database, config: ConfigStore
) -> None:
    if callback.from_user is None or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.ADMIN_ONLY, show_alert=True)
        return
    if callback.data is None or not isinstance(callback.message, Message):
        await callback.answer()
        return

    action = callback.data.split(":", 1)[1]

    if action == "voice":
        on = not await config.voice_enabled()
        await config.set_voice_enabled(on)
        await callback.answer(texts.admin_voice_toggled(on))
        await callback.message.edit_text(
            await _panel_text(db, config),
            reply_markup=keyboards.admin_panel_keyboard(voice_on=on),
        )
    elif action in {"back", "refresh"}:
        await callback.answer()
        await callback.message.edit_text(
            await _panel_text(db, config),
            reply_markup=keyboards.admin_panel_keyboard(
                voice_on=await config.voice_enabled()
            ),
        )
    elif action == "models":
        await callback.answer()
        await callback.message.edit_text(
            texts.ADMIN_MODELS_TITLE,
            reply_markup=keyboards.admin_models_keyboard(
                await _all_models(config), await config.disabled_models()
            ),
        )


@router.callback_query(F.data.startswith(f"{keyboards.CB_ADMIN_MODEL}:"))
async def on_admin_model_toggle(
    callback: CallbackQuery, settings: Settings, config: ConfigStore
) -> None:
    if callback.from_user is None or not settings.is_admin(callback.from_user.id):
        await callback.answer(texts.ADMIN_ONLY, show_alert=True)
        return
    if callback.data is None or not isinstance(callback.message, Message):
        await callback.answer()
        return

    pool = await _all_models(config)
    try:
        idx = int(callback.data.split(":", 1)[1])
        model = pool[idx]
    except (ValueError, IndexError):
        await callback.answer("Unknown model.", show_alert=True)
        return

    disabled = await config.disabled_models()
    if model in disabled:
        disabled.discard(model)
        enabled = True
    else:
        disabled.add(model)
        enabled = False
    await config.set_disabled_models(sorted(disabled))
    await callback.answer(texts.admin_model_toggled(model, enabled))
    await callback.message.edit_reply_markup(
        reply_markup=keyboards.admin_models_keyboard(pool, disabled)
    )
