"""Core conversational handlers: plain text and voice messages → AI reply.

Both entry points funnel into :func:`respond`, which enforces the daily quota,
shows a "thinking…" placeholder, generates a reply through :class:`ChatService`
(memory + model rotation) and edits the placeholder into the answer — or into a
graceful "all models busy" message (with an upgrade nudge for free users) when
every model in the pool is unavailable.
"""

from __future__ import annotations

import asyncio
import base64
import io
import logging
import re
from collections.abc import Awaitable, Callable

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from aiogram.utils.chat_action import ChatActionSender

from ...config import Settings
from ...core import ChatService, ConfigStore, LLMError, Transcriber
from ...core.ports import Completion
from ...db import Database, repo
from ...db.models import User
from .. import texts
from ..formatting import to_telegram_html

router = Router(name="chat")
log = logging.getLogger(__name__)

_TG_LIMIT = 4096  # Telegram hard-caps message text at 4096 chars.
_HINT_DELAY = 4.0  # seconds before the "go Premium" nudge appears on Thinking…


async def _thinking_hint(placeholder: Message) -> None:
    """After a short delay, append an italic upsell to the Thinking… message."""
    try:
        await asyncio.sleep(_HINT_DELAY)
        await placeholder.edit_text(texts.THINKING_UPSELL)
    except asyncio.CancelledError:
        raise
    except Exception:  # noqa: BLE001 - the nudge is best-effort, never fatal
        pass


async def _cancel(task: "asyncio.Task[None] | None") -> None:
    """Cancel the hint task and wait for it, so edits stay correctly ordered."""
    if task is None:
        return
    task.cancel()
    try:
        await task
    except (asyncio.CancelledError, Exception):  # noqa: BLE001
        pass


@router.message(F.text & ~F.text.startswith("/"))
async def on_text(
    message: Message,
    db: Database,
    service: ChatService,
    config: ConfigStore,
) -> None:
    if message.from_user is None or not message.text:
        return
    text = message.text
    await respond(message, db, config, service, lambda u: service.reply(u, text))


@router.message(F.photo)
async def on_photo(
    message: Message,
    db: Database,
    service: ChatService,
    config: ConfigStore,
) -> None:
    if message.from_user is None or not message.photo:
        return
    if not await config.vision_enabled():
        await message.answer(texts.VISION_DISABLED)
        return
    # Largest available size is last; download to memory and build a data URL.
    bot: Bot = message.bot  # type: ignore[assignment]
    buffer = io.BytesIO()
    try:
        await bot.download(message.photo[-1], destination=buffer)
    except Exception as exc:  # noqa: BLE001
        log.warning("photo download failed for tg=%s: %s", message.from_user.id, exc)
        await message.answer(texts.ERROR_GENERIC)
        return
    data_url = "data:image/jpeg;base64," + base64.b64encode(buffer.getvalue()).decode()
    caption = message.caption or ""
    await respond(
        message, db, config, service, lambda u: service.reply_image(u, data_url, caption)
    )


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
    await respond(message, db, config, service, lambda u: service.reply(u, text))


async def respond(
    message: Message,
    db: Database,
    config: ConfigStore,
    service: ChatService,
    generate: Callable[[User], Awaitable[Completion]],
) -> None:
    """Shared reply path: gate (ban/pause/quota), think, generate, deliver."""
    tg = message.from_user
    assert tg is not None

    async with db.session() as session:
        user = await repo.get_or_create_user(
            session, tg.id, username=tg.username, first_name=tg.first_name
        )
        used = await repo.used_today(session, tg.id)
        is_premium = user.is_premium
        banned = user.banned
        override = user.limit_override
        user_obj = user

    # Blocked/frozen by an admin — don't generate anything.
    if banned:
        await message.answer(texts.BANNED)
        return

    # Global kill-switch (admin paused the bot).
    if await config.generation_paused():
        await message.answer(texts.PAUSED)
        return

    tier_cfg = await config.tier_for_user(user_obj)
    limit = override if override is not None else tier_cfg.daily_limit

    if used >= limit:
        tier = "premium" if is_premium else "free"
        await message.answer(texts.limit_reached(tier, limit))
        return

    # Immediate feedback: a placeholder we always resolve into an answer or a
    # clear error — it must never be left hanging as "Thinking…".
    placeholder = await message.answer(texts.THINKING)
    timeout = service.settings.reply_timeout

    # If generation takes a while, append an italic "go Premium for faster
    # replies" nudge to the placeholder — but only for free users who actually
    # have a paid plan to upgrade to.
    show_hint = not is_premium and bool(await config.paid_tiers())
    hint_task = (
        asyncio.create_task(_thinking_hint(placeholder)) if show_hint else None
    )

    try:
        async with ChatActionSender(
            bot=message.bot, chat_id=message.chat.id, action=ChatAction.TYPING
        ):
            completion = await asyncio.wait_for(
                generate(user_obj), timeout=timeout
            )
    except (LLMError, asyncio.TimeoutError) as exc:
        # No model answered in time / all busy — nudge free users to upgrade.
        await _cancel(hint_task)
        log.warning("generation unavailable for tg=%s: %r", tg.id, exc)
        await _safe_edit(placeholder, texts.all_busy(is_premium))
        return
    except Exception:  # noqa: BLE001 - never leave the user hanging
        await _cancel(hint_task)
        log.exception("unexpected error generating reply for tg=%s", tg.id)
        await _safe_edit(placeholder, texts.ERROR_GENERIC)
        return

    await _cancel(hint_task)

    # The model replies in Markdown; render it to Telegram-safe HTML.
    html_text = to_telegram_html(completion.text)
    chunks = _split_message(html_text)
    await _safe_edit(placeholder, chunks[0])
    for chunk in chunks[1:]:
        await _send_html(message, chunk)


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


def _strip_tags(text: str) -> str:
    return re.sub(r"<[^>]+>", "", text)


async def _safe_edit(message: Message, text: str) -> None:
    """Edit with HTML; on a parse/edit failure, fall back to plain text."""
    try:
        await message.edit_text(text)
        return
    except TelegramBadRequest:
        pass
    except Exception:  # noqa: BLE001
        pass
    try:
        await message.edit_text(_strip_tags(text), parse_mode=None)
    except Exception:  # noqa: BLE001 - last resort: a fresh plain message
        await message.answer(_strip_tags(text), parse_mode=None)


async def _send_html(message: Message, text: str) -> None:
    try:
        await message.answer(text)
    except TelegramBadRequest:
        await message.answer(_strip_tags(text), parse_mode=None)


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
