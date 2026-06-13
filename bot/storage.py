"""Lightweight per-user persistence backed by SQLite (via aiosqlite).

We store only what the bot itself needs to operate: the user's tier, daily
usage counters with a rolling reset, their selected model and a short rolling
chat history used as the prompt window. Long-term *memory* lives in the GetMem
service — this database is intentionally small and disposable.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import aiosqlite

# UTC day bucket. Usage counters reset when the day bucket changes.
_DAY = 86_400


def _today() -> int:
    return int(time.time()) // _DAY


@dataclass
class User:
    user_id: int
    tier: str  # "free" | "premium"
    model: str | None  # preferred model override, or None for auto-rotation
    daily_count: int
    day_bucket: int
    premium_until: int  # unix ts; 0 = never
    created_at: int

    @property
    def is_premium(self) -> bool:
        return self.tier == "premium" and (
            self.premium_until == 0 or self.premium_until > int(time.time())
        )


_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    user_id       INTEGER PRIMARY KEY,
    tier          TEXT    NOT NULL DEFAULT 'free',
    model         TEXT,
    daily_count   INTEGER NOT NULL DEFAULT 0,
    day_bucket    INTEGER NOT NULL DEFAULT 0,
    premium_until INTEGER NOT NULL DEFAULT 0,
    created_at    INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS history (
    user_id   INTEGER NOT NULL,
    role      TEXT    NOT NULL,
    content   TEXT    NOT NULL,
    ts        INTEGER NOT NULL,
    PRIMARY KEY (user_id, ts)
);

CREATE TABLE IF NOT EXISTS payments (
    charge_id    TEXT PRIMARY KEY,
    user_id      INTEGER NOT NULL,
    amount_stars INTEGER NOT NULL,
    ts           INTEGER NOT NULL
);
"""


class Storage:
    """Async SQLite store. One instance shared across the app."""

    def __init__(self, db_path: str) -> None:
        self._db_path = db_path
        self._db: aiosqlite.Connection | None = None

    async def connect(self) -> None:
        self._db = await aiosqlite.connect(self._db_path)
        self._db.row_factory = aiosqlite.Row
        await self._db.executescript(_SCHEMA)
        await self._db.commit()

    async def close(self) -> None:
        if self._db is not None:
            await self._db.close()
            self._db = None

    @property
    def db(self) -> aiosqlite.Connection:
        if self._db is None:
            raise RuntimeError("Storage.connect() was not awaited")
        return self._db

    # -- users -----------------------------------------------------------

    async def get_or_create_user(self, user_id: int) -> User:
        row = await (
            await self.db.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            )
        ).fetchone()
        if row is None:
            now = int(time.time())
            await self.db.execute(
                "INSERT INTO users (user_id, day_bucket, created_at) "
                "VALUES (?, ?, ?)",
                (user_id, _today(), now),
            )
            await self.db.commit()
            return User(user_id, "free", None, 0, _today(), 0, now)
        return self._row_to_user(row)

    @staticmethod
    def _row_to_user(row: aiosqlite.Row) -> User:
        return User(
            user_id=row["user_id"],
            tier=row["tier"],
            model=row["model"],
            daily_count=row["daily_count"],
            day_bucket=row["day_bucket"],
            premium_until=row["premium_until"],
            created_at=row["created_at"],
        )

    async def set_model(self, user_id: int, model: str | None) -> None:
        await self.db.execute(
            "UPDATE users SET model = ? WHERE user_id = ?", (model, user_id)
        )
        await self.db.commit()

    async def grant_premium(self, user_id: int, until_ts: int) -> None:
        await self.get_or_create_user(user_id)
        await self.db.execute(
            "UPDATE users SET tier = 'premium', premium_until = ? "
            "WHERE user_id = ?",
            (until_ts, user_id),
        )
        await self.db.commit()

    async def consume_quota(self, user_id: int) -> User:
        """Increment today's usage counter, resetting it across day boundaries.

        Returns the refreshed user so callers see the post-increment count.
        """
        user = await self.get_or_create_user(user_id)
        today = _today()
        if user.day_bucket != today:
            count = 1
            await self.db.execute(
                "UPDATE users SET daily_count = 1, day_bucket = ? "
                "WHERE user_id = ?",
                (today, user_id),
            )
        else:
            count = user.daily_count + 1
            await self.db.execute(
                "UPDATE users SET daily_count = daily_count + 1 "
                "WHERE user_id = ?",
                (user_id,),
            )
        await self.db.commit()
        user.daily_count = count
        user.day_bucket = today
        return user

    async def remaining_today(self, user_id: int, limit: int) -> int:
        user = await self.get_or_create_user(user_id)
        used = user.daily_count if user.day_bucket == _today() else 0
        return max(0, limit - used)

    # -- history ---------------------------------------------------------

    async def add_history(self, user_id: int, role: str, content: str) -> None:
        await self.db.execute(
            "INSERT OR REPLACE INTO history (user_id, role, content, ts) "
            "VALUES (?, ?, ?, ?)",
            (user_id, role, content, time.time_ns()),
        )
        await self.db.commit()

    async def get_history(
        self, user_id: int, limit_turns: int
    ) -> list[dict[str, str]]:
        # ``limit_turns`` is conversational turns; fetch 2x rows (user+assistant).
        rows = await (
            await self.db.execute(
                "SELECT role, content FROM history WHERE user_id = ? "
                "ORDER BY ts DESC LIMIT ?",
                (user_id, limit_turns * 2),
            )
        ).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    async def clear_history(self, user_id: int) -> None:
        await self.db.execute(
            "DELETE FROM history WHERE user_id = ?", (user_id,)
        )
        await self.db.commit()

    # -- payments --------------------------------------------------------

    async def record_payment(
        self, charge_id: str, user_id: int, amount_stars: int
    ) -> None:
        await self.db.execute(
            "INSERT OR IGNORE INTO payments "
            "(charge_id, user_id, amount_stars, ts) VALUES (?, ?, ?, ?)",
            (charge_id, user_id, amount_stars, int(time.time())),
        )
        await self.db.commit()

    async def stats(self) -> dict[str, int]:
        async def scalar(sql: str) -> int:
            cur = await self.db.execute(sql)
            row = await cur.fetchone()
            return int(row[0]) if row else 0

        return {
            "users": await scalar("SELECT COUNT(*) FROM users"),
            "premium": await scalar(
                "SELECT COUNT(*) FROM users WHERE tier = 'premium'"
            ),
            "messages_today": await scalar(
                f"SELECT COALESCE(SUM(daily_count),0) FROM users "
                f"WHERE day_bucket = {_today()}"
            ),
            "payments": await scalar("SELECT COUNT(*) FROM payments"),
        }
