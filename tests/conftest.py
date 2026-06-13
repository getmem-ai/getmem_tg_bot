import os

import pytest

from bot.config import Settings, load_settings
from bot.storage import Storage


@pytest.fixture
def settings() -> Settings:
    os.environ.setdefault("BOT_TOKEN", "test-token")
    os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
    return load_settings()


@pytest.fixture
async def storage(tmp_path) -> Storage:
    store = Storage(str(tmp_path / "test.db"))
    await store.connect()
    try:
        yield store
    finally:
        await store.close()
