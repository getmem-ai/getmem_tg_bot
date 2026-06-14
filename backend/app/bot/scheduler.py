"""Background scheduler — fires users' recurring reminders in their local time.

A single asyncio task (started alongside the bot) polls for due
:class:`ScheduledTask` rows, runs each through the model proactively
(:meth:`ChatService.run_scheduled`), pushes the result to the user, logs a
:class:`ScheduledRun`, and recomputes the task's next fire time in the user's
timezone. Missed fires (e.g. downtime) collapse to a single catch-up run.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import logging
import re

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from ..core import ChatService, ConfigStore
from ..core.scheduling import compute_next_run
from ..db import Database, repo
from .formatting import to_telegram_html

log = logging.getLogger(__name__)

_POLL_INTERVAL = 30.0
_TG_LIMIT = 4096


def _split(text: str) -> list[str]:
    if len(text) <= _TG_LIMIT:
        return [text]
    out, rest = [], text
    while len(rest) > _TG_LIMIT:
        cut = rest.rfind("\n", 0, _TG_LIMIT)
        if cut <= 0:
            cut = _TG_LIMIT
        out.append(rest[:cut])
        rest = rest[cut:].lstrip("\n")
    if rest:
        out.append(rest)
    return out


async def _send(bot: Bot, chat_id: int, html: str) -> None:
    try:
        await bot.send_message(chat_id, html)
    except TelegramBadRequest:
        # HTML failed to parse — send plain text instead.
        await bot.send_message(chat_id, re.sub(r"<[^>]+>", "", html))


async def run_scheduler(
    *,
    bot: Bot,
    db: Database,
    service: ChatService,
    config: ConfigStore,
    poll_interval: float = _POLL_INTERVAL,
) -> None:
    log.info("Scheduler started (poll every %.0fs)", poll_interval)
    while True:
        try:
            await _tick(bot, db, service, config)
        except asyncio.CancelledError:
            raise
        except Exception:  # noqa: BLE001 - the loop must survive any failure
            log.exception("scheduler tick failed")
        await asyncio.sleep(poll_interval)


async def _tick(
    bot: Bot, db: Database, service: ChatService, config: ConfigStore
) -> None:
    if not await config.scheduling_enabled():
        return
    now = dt.datetime.now(dt.timezone.utc)
    async with db.session() as session:
        due = await repo.due_tasks(session, now, limit=25)
    for task in due:
        await _fire(bot, db, service, task, now)


async def _fire(bot, db, service, task, now):  # type: ignore[no-untyped-def]
    async with db.session() as session:
        user = await repo.get_user(session, task.user_id)

    nxt = (
        compute_next_run(
            timezone=getattr(user, "timezone", "UTC") or "UTC",
            frequency=task.frequency,
            times=task.times or [],
            weekdays=task.weekdays or [],
            after=now,
        )
        if user is not None
        else None
    )

    # Orphaned or blocked task — advance/disable without sending.
    if user is None:
        await _update_task(db, task.id, last=None, nxt=None, disable=True)
        return
    if user.banned:
        await _update_task(db, task.id, last=now, nxt=nxt, disable=nxt is None)
        return

    status, preview = "sent", ""
    try:
        completion = await service.run_scheduled(user, task.prompt)
        for chunk in _split(to_telegram_html(completion.text)):
            await _send(bot, task.user_id, chunk)
        preview = completion.text[:500]
    except TelegramForbiddenError:
        # User blocked the bot — stop bothering them.
        log.info("user %s blocked the bot; disabling task %s", task.user_id, task.id)
        await _update_task(db, task.id, last=now, nxt=None, disable=True)
        async with db.session() as session:
            await repo.add_run(
                session,
                task_id=task.id,
                user_id=task.user_id,
                status="failed",
                preview="user blocked the bot",
            )
        return
    except Exception as exc:  # noqa: BLE001 - record and keep the schedule alive
        status, preview = "failed", str(exc)[:500]
        log.warning("scheduled task %s failed: %r", task.id, exc)

    await _update_task(db, task.id, last=now, nxt=nxt, disable=nxt is None)
    async with db.session() as session:
        await repo.add_run(
            session,
            task_id=task.id,
            user_id=task.user_id,
            status=status,
            preview=preview,
        )


async def _update_task(db, task_id, *, last, nxt, disable):  # type: ignore[no-untyped-def]
    async with db.session() as session:
        task = await repo.get_task(session, task_id)
        if task is None:
            return
        if last is not None:
            task.last_run_at = last
        task.next_run_at = nxt
        if disable:
            task.enabled = False
