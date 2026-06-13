"""Bot wiring and run loop (long polling or webhook).

Builds the aiogram :class:`Dispatcher`, injects shared dependencies (settings,
database, memory, LLM, transcriber, chat service), registers the command menu
and the Mini App menu button, then runs. The API runs as a separate process;
this module owns only the Telegram side.
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import (
    BotCommand,
    MenuButtonDefault,
    MenuButtonWebApp,
    WebAppInfo,
)

from ..config import Settings
from ..container import Container
from ..core.ports import MemoryStore
from .handlers import build_router

log = logging.getLogger(__name__)

_COMMANDS = [
    BotCommand(command="start", description="Start / intro"),
    BotCommand(command="help", description="What I can do"),
    BotCommand(command="me", description="Your plan & usage"),
    BotCommand(command="model", description="Choose the AI model"),
    BotCommand(command="app", description="Open your dashboard"),
    BotCommand(command="upgrade", description="Unlock premium ⭐"),
    BotCommand(command="reset", description="Clear recent chat window"),
    BotCommand(command="forget", description="Erase long-term memory"),
]


async def _on_startup(bot: Bot, settings: Settings, memory: MemoryStore) -> None:
    await bot.set_my_commands(_COMMANDS)

    # Wire the Mini App as the chat menu button (HTTPS only — Telegram rejects
    # plain HTTP web_app URLs).
    if settings.miniapp_url.startswith("https://"):
        await bot.set_chat_menu_button(
            menu_button=MenuButtonWebApp(
                text="Dashboard", web_app=WebAppInfo(url=settings.miniapp_url)
            )
        )
    else:
        await bot.set_chat_menu_button(menu_button=MenuButtonDefault())

    me = await bot.get_me()
    healthy = await memory.healthy() if memory.enabled else False
    log.info(
        "Bot @%s started. Memory: %s | Mini App: %s",
        me.username,
        "connected"
        if healthy
        else ("enabled (unverified)" if memory.enabled else "disabled"),
        settings.miniapp_url or "not set",
    )


async def run_bot(container: Container) -> None:
    """Run the Telegram bot using dependencies from the DI container."""
    settings = container.settings

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(build_router())

    # Dependency injection: aiogram passes these to any handler that declares a
    # parameter with a matching name. Handlers depend on the port types.
    dp["settings"] = settings
    dp["db"] = container.db
    dp["memory"] = container.memory
    dp["service"] = container.chat_service
    dp["transcriber"] = container.transcriber
    dp["runtime"] = container.runtime

    try:
        await _on_startup(bot, settings, container.memory)
        if settings.use_webhook:
            await _run_webhook(bot, dp, settings)
        else:
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot)
    finally:
        await bot.session.close()


async def _run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    """Serve updates over a webhook (public domain behind TLS via Caddy)."""
    from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
    from aiohttp import web

    url = settings.webhook_url.rstrip("/") + settings.webhook_path
    await bot.set_webhook(
        url=url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    log.info("Webhook set to %s", url)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp, bot=bot, secret_token=settings.webhook_secret or None
    ).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    log.info("Webhook server listening on %s:%s", settings.web_host, settings.web_port)
    await asyncio.Event().wait()
