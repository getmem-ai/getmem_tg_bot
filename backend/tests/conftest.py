import os

import pytest

from app.config import Settings, load_settings


@pytest.fixture
def settings() -> Settings:
    os.environ.setdefault("BOT_TOKEN", "123456:test-bot-token")
    os.environ.setdefault("OPENROUTER_API_KEY", "test-key")
    return load_settings()
