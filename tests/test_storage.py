import time


from bot.storage import Storage, User, _today


async def test_get_or_create_is_idempotent(storage: Storage) -> None:
    u1 = await storage.get_or_create_user(42)
    u2 = await storage.get_or_create_user(42)
    assert u1.user_id == u2.user_id == 42
    assert u1.tier == "free"
    assert not u1.is_premium


async def test_quota_increments_and_resets_across_days(storage: Storage) -> None:
    for expected in (1, 2, 3):
        user = await storage.consume_quota(7)
        assert user.daily_count == expected

    # Simulate yesterday's bucket → next consume resets to 1.
    await storage.db.execute(
        "UPDATE users SET day_bucket = ? WHERE user_id = 7", (_today() - 1,)
    )
    await storage.db.commit()
    user = await storage.consume_quota(7)
    assert user.daily_count == 1


async def test_remaining_today(storage: Storage) -> None:
    await storage.consume_quota(9)
    await storage.consume_quota(9)
    assert await storage.remaining_today(9, limit=30) == 28


async def test_history_roundtrip_and_window(storage: Storage) -> None:
    for i in range(5):
        await storage.add_history(3, "user", f"q{i}")
        await storage.add_history(3, "assistant", f"a{i}")
    hist = await storage.get_history(3, limit_turns=2)
    # 2 turns → up to 4 messages, oldest-first, most recent kept.
    assert len(hist) == 4
    assert hist[-1] == {"role": "assistant", "content": "a4"}
    assert hist[0]["content"] in {"q3", "a3"}

    await storage.clear_history(3)
    assert await storage.get_history(3, limit_turns=10) == []


async def test_grant_premium(storage: Storage) -> None:
    until = int(time.time()) + 3600
    await storage.grant_premium(5, until)
    user = await storage.get_or_create_user(5)
    assert user.is_premium
    assert user.tier == "premium"


async def test_expired_premium_is_not_premium() -> None:
    user = User(1, "premium", None, 0, 0, premium_until=int(time.time()) - 10, created_at=0)
    assert not user.is_premium


async def test_record_payment_dedupes(storage: Storage) -> None:
    await storage.record_payment("charge_1", 1, 250)
    await storage.record_payment("charge_1", 1, 250)
    stats = await storage.stats()
    assert stats["payments"] == 1
