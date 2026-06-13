"""Core conversational handlers: plain text and voice messages → AI reply.

Both entry points funnel into :func:`respond`, which enforces the daily quota,
shows a "thinking…" placeholder, generates a reply through :class:`ChatService`
(memory + model rotation) and edits the placeholder into the answer — or into a
graceful "all models busy" message (with an upgrade nudge for free users) when
every model in the pool is unavailable.
"""

from __future__ import annotations

import asyncio
import io
import logging

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from ...config import Settings
from ...core import ChatService, ConfigStore, LLMError, Transcriber
from ...db import Database, repo
from .. import texts

router = Router(name="chat")
log = logging.getLogger(__name__)

_TG_LIMIT = 4096  # Telegram hard-caps message text at 4096 chars.


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(
    message: Message,
    db: Database,
    service: ChatService,
    config: ConfigStore,
) -> None:
    if message.from_user is None or not message.text:
        return
    await respond(message, message.text, db, service, config)


@router.message(F.voice | F.audio)
async def on_voice(
    message: Message,
    settings: Settings,
    db: Database,
    service: ChatService,
    config: ConfigStore,
    transcriber: Transcriber,
) -> None:
    if message.from_user is None:
        return
    if not await config.voice_enabled():
        await message.answer(texts.VOICE_DISABLED)
        return

    media = message.voice or message.audio
    if media is None:
        return
    if media.duration and media.duration > settings.voice_max_duration:
        await message.answer(texts.voice_too_long(settings.voice_max_duration))
        return

    text = await _transcribe_message(message, transcriber)
    if not text:
        await message.answer(texts.VOICE_EMPTY)
        return

    # Show the user what we heard, then answer it like any other message.
    await message.answer(texts.voice_heard(text))
    await respond(message, text, db, service, config)


async def respond(
    message: Message,
    user_text: str,
    db: Database,
    service: ChatService,
    config: ConfigStore,
) -> None:
    """Shared reply path for text and transcribed voice."""
    tg = message.from_user
    assert tg is not None

    async with db.session() as session:
        user = await repo.get_or_create_user(
            session, tg.id, username=tg.username, first_name=tg.first_name
        )
        used = await repo.used_today(session, tg.id)
        is_premium = user.is_premium
        user_obj = user

    limit = (await config.tier_for_user(user_obj)).daily_limit

    if used >= limit:
        tier = "premium" if is_premium else "free"
        await message.answer(texts.limit_reached(tier, limit))
        return

    # Immediate feedback: a placeholder we always resolve into an answer or a
    # clear error — it must never be left hanging as "Thinking…".
    placeholder = await message.answer(texts.THINKING)
    timeout = service.settings.reply_timeout

    try:
        async with ChatActionSender(
            bot=message.bot, chat_id=message.chat.id, action=ChatAction.TYPING
        ):
            completion = await asyncio.wait_for(
                service.reply(user_obj, user_text), timeout=timeout
            )
    except (LLMError, asyncio.TimeoutError) as exc:
        # No model answered in time / all busy — nudge free users to upgrade.
        log.warning("generation unavailable for tg=%s: %r", tg.id, exc)
        await _safe_edit(placeholder, texts.all_busy(is_premium))
        return
    except Exception:  # noqa: BLE001 - never leave the user hanging
        log.exception("unexpected error generating reply for tg=%s", tg.id)
        await _safe_edit(placeholder, texts.ERROR_GENERIC)
        return

    chunks = _split_message(completion.text)
    await _safe_edit(placeholder, chunks[0])
    for chunk in chunks[1:]:
        await message.answer(chunk)


async def _transcribe_message(message: Message, transcriber: Transcriber) -> str:
    bot: Bot = message.bot  # type: ignore[assignment]
    media = message.voice or message.audio
    assert media is not None

    try:
        buffer = io.BytesIO()
        await bot.download(media, destination=buffer)
        audio = buffer.getvalue()
        filename = "voice.oga" if message.voice else "audio"
        async with ChatActionSender(
            bot=bot, chat_id=message.chat.id, action=ChatAction.TYPING
        ):
            return await transcriber.transcribe(audio, filename=filename)
    except Exception as exc:  # noqa: BLE001 - report a friendly error, keep bot up
        log.warning("transcription failed for tg=%s: %s", message.from_user.id, exc)  # type: ignore[union-attr]
        return ""


async def _safe_edit(message: Message, text: str) -> None:
    try:
        await message.edit_text(text)
    except Exception:  # noqa: BLE001 - fall back to a fresh message
        await message.answer(text)


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
