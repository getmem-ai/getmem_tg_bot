"""Bot process entrypoint:  ``python -m app.entrypoints.bot``."""

from __future__ import annotations

import asyncio
import logging

from ..bot import run_bot
from ..config import load_settings
from ..container import Container

log = logging.getLogger(__name__)


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    settings = load_settings()

    async def _run() -> None:
        container = Container(settings)
        try:
            await run_bot(container)
        finally:
            await container.aclose()

    try:
        asyncio.run(_run())
    except (KeyboardInterrupt, SystemExit):
        log.info("Shutting down.")


if __name__ == "__main__":
    main()
