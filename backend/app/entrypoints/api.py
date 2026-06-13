"""API process entrypoint:  ``python -m app.entrypoints.api``.

Equivalent to ``uvicorn app.api.app:app`` but reads host/port from settings.
"""

from __future__ import annotations

import logging

import uvicorn

from ..config import load_settings


def main() -> None:
    # The bot token isn't strictly needed to import the API, but it IS needed
    # to validate Telegram initData, so require it here too.
    settings = load_settings(require_openrouter=False)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-8s %(name)s: %(message)s",
    )
    uvicorn.run(
        "app.api.app:app",
        host=settings.api_host,
        port=settings.api_port,
        proxy_headers=True,
        forwarded_allow_ips="*",
    )


if __name__ == "__main__":
    main()
