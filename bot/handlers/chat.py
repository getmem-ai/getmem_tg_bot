"""The core conversational handler: any plain text message → AI reply."""

from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from .. import texts
from ..config import Settings
from ..limits import daily_limit
from ..llm import LLMError
from ..service import ChatService

router = Router(name="chat")
log = logging.getLogger(__name__)

# Telegram hard-caps message text at 4096 chars.
_TG_LIMIT = 4096


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(
    message: Message,
    settings: Settings,
    service: ChatService,
) -> None:
    if message.from_user is None or not message.text:
        return
    tg_id = message.from_user.id

    user = await service.storage.get_or_create_user(tg_id)

    # Enforce the per-tier daily quota *before* spending a model call.
    limit = daily_limit(settings, user)
    remaining = await service.storage.remaining_today(tg_id, limit)
    if remaining <= 0:
        await message.answer(texts.limit_reached(user.tier, limit))
        return

    try:
        async with ChatActionSender(
            bot=message.bot, chat_id=message.chat.id, action=ChatAction.TYPING
        ):
            completion = await service.reply(user, message.text)
    except LLMError as exc:
        log.warning("generation failed for tg=%s: %s", tg_id, exc)
        await message.answer(texts.ERROR_GENERIC)
        return

    # Only consume quota on a successful reply.
    await service.storage.consume_quota(tg_id)

    for chunk in _split_message(completion.text):
        await message.answer(chunk)


def _split_message(text: str) -> list[str]:
    """Split long replies to respect Telegram's 4096-char limit."""
    if len(text) <= _TG_LIMIT:
        return [text]
    chunks: list[str] = []
    remaining = text
    while len(remaining) > _TG_LIMIT:
        cut = remaining.rfind("\n", 0, _TG_LIMIT)
        if cut <= 0:
            cut = _TG_LIMIT
        chunks.append(remaining[:cut])
        remaining = remaining[cut:].lstrip("\n")
    if remaining:
        chunks.append(remaining)
    return chunks
