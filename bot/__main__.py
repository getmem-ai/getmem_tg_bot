"""Application entrypoint: wire dependencies and run the bot (long polling).

Run with::

    python -m bot

All configuration comes from the environment (see ``bot/config.py`` and
``.env.example``). The bot uses long polling by default, which needs no inbound
ports, no domain and no TLS — ideal for a single-server deployment behind any
network. (A webhook variant is easy to add later; polling keeps setup trivial.)
"""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from .config import Settings, load_settings
from .handlers import build_router
from .llm import LLMClient
from .memory import Memory
from .service import ChatService
from .storage import Storage

log = logging.getLogger(__name__)

_COMMANDS = [
    BotCommand(command="start", description="Start / intro"),
    BotCommand(command="help", description="What I can do"),
    BotCommand(command="me", description="Your plan & usage"),
    BotCommand(command="model", description="Choose the AI model"),
    BotCommand(command="upgrade", description="Unlock premium ⭐"),
    BotCommand(command="reset", description="Clear recent chat window"),
    BotCommand(command="forget", description="Erase long-term memory"),
]


async def _on_startup(bot: Bot, memory: Memory) -> None:
    await bot.set_my_commands(_COMMANDS)
    me = await bot.get_me()
    healthy = await memory.healthy() if memory.enabled else False
    log.info(
        "Bot @%s started. Memory: %s",
        me.username,
        "connected" if healthy else ("enabled (unverified)" if memory.enabled else "disabled"),
    )


async def run(settings: Settings) -> None:
    storage = Storage(settings.db_path)
    await storage.connect()

    memory = Memory(
        settings.getmem_api_key,
        base_url=settings.getmem_base_url,
        token_budget=settings.memory_token_budget,
    )
    llm = LLMClient(
        settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.request_timeout,
        app_url=settings.app_url,
        app_name=settings.app_name,
    )
    service = ChatService(settings, storage, memory, llm)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(build_router())

    # Dependency injection: aiogram passes these to any handler that declares a
    # parameter with the matching name.
    dp["settings"] = settings
    dp["storage"] = storage
    dp["memory"] = memory
    dp["service"] = service

    try:
        await _on_startup(bot, memory)
        if settings.use_webhook:
            await _run_webhook(bot, dp, settings)
        else:
            # Polling needs no domain, ports or TLS — the default.
            await bot.delete_webhook(drop_pending_updates=False)
            await dp.start_polling(bot)
    finally:
        await llm.close()
        await memory.close()
        await storage.close()
        await bot.session.close()


async def _run_webhook(bot: Bot, dp: Dispatcher, settings: Settings) -> None:
    """Serve updates over a webhook (for a public domain behind TLS).

    The bot listens on plain HTTP; terminate TLS in front of it (the bundled
    Caddy reverse proxy in ``deploy/`` does this automatically via Let's
    Encrypt). See ``deploy/README.md``.
    """
    from aiohttp import web
    from aiogram.webhook.aiohttp_server import (
        SimpleRequestHandler,
        setup_application,
    )

    url = settings.webhook_url.rstrip("/") + settings.webhook_path
    await bot.set_webhook(
        url=url,
        secret_token=settings.webhook_secret or None,
        drop_pending_updates=True,
    )
    log.info("Webhook set to %s", url)

    app = web.Application()
    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook_secret or None,
    ).register(app, path=settings.webhook_path)
    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, settings.web_host, settings.web_port)
    await site.start()
    log.info("Listening on %s:%s", settings.web_host, settings.web_port)
    # Sleep forever; the finally-block in run() handles cleanup on cancel.
    await asyncio.Event().wait()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    settings = load_settings()
    try:
        asyncio.run(run(settings))
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
