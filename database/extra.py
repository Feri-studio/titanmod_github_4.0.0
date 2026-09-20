"""Extra tables: XP, giveaways, aliases, quarantine, watches."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

import aiosqlite

from config import config

DB_PATH = config.DB_PATH

EXTRA_SCHEMA = [
    """
    CREATE TABLE IF NOT EXISTS xp (
        chat_id INTEGER,
        user_id INTEGER,
        xp INTEGER DEFAULT 0,
        level INTEGER DEFAULT 1,
        messages INTEGER DEFAULT 0,
        last_xp REAL DEFAULT 0,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS giveaways (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        admin_id INTEGER,
        prize TEXT,
        winners INTEGER DEFAULT 1,
        message_id INTEGER,
        closes_at REAL,
        closed INTEGER DEFAULT 0,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS giveaway_members (
        giveaway_id INTEGER,
        user_id INTEGER,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (giveaway_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS aliases (
        chat_id INTEGER,
        alias TEXT,
        command TEXT,
        PRIMARY KEY (chat_id, alias)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS quarantine (
        chat_id INTEGER,
        user_id INTEGER,
        until_ts REAL,
        reason TEXT,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS watches (
        chat_id INTEGER,
        user_id INTEGER,
        admin_id INTEGER,
        note TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (chat_id, user_id)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS prefixes (
        chat_id INTEGER PRIMARY KEY,
        prefix TEXT
    )
    """,
]


def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


async def init_extra():
    async with aiosqlite.connect(DB_PATH) as db:
        for stmt in EXTRA_SCHEMA:
            await db.execute(stmt)
        await db.commit()


async def add_xp(chat_id: int, user_id: int, amount: int, cooldown: int = 45) -> tuple[int, int, bool]:
    """Returns (xp, level, leveled_up)."""
    import time
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT xp, level, last_xp, messages FROM xp WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO xp (chat_id, user_id, xp, level, messages, last_xp) VALUES (?,?,?,?,?,?)",
                (chat_id, user_id, amount, 1, 1, now),
            )
            await db.commit()
            return amount, 1, False
        if now - (row["last_xp"] or 0) < cooldown:
            await db.execute(
                "UPDATE xp SET messages=messages+1 WHERE chat_id=? AND user_id=?",
                (chat_id, user_id),
            )
            await db.commit()
            return row["xp"], row["level"], False
        xp = row["xp"] + amount
        level = 1
        need = 0
        while True:
            need += 80 + level * 35
            if xp < need:
                break
            level += 1
            if level > 200:
                break
        leveled = level > row["level"]
        await db.execute(
            "UPDATE xp SET xp=?, level=?, messages=messages+1, last_xp=? WHERE chat_id=? AND user_id=?",
            (xp, level, now, chat_id, user_id),
        )
        await db.commit()
        return xp, level, leveled


async def get_xp(chat_id: int, user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM xp WHERE chat_id=? AND user_id=?", (chat_id, user_id)
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def set_xp(chat_id: int, user_id: int, xp: int):
    level = 1
    need = 0
    while True:
        need += 80 + level * 35
        if xp < need or level >= 200:
            break
        level += 1
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO xp (chat_id, user_id, xp, level, messages, last_xp)
            VALUES (?,?,?,?,0,0)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET xp=excluded.xp, level=excluded.level
            """,
            (chat_id, user_id, xp, level),
        )
        await db.commit()
        return level


async def top_xp(chat_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM xp WHERE chat_id=? ORDER BY xp DESC LIMIT ?",
            (chat_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def reset_xp(chat_id: int, user_id: int | None = None):
    async with aiosqlite.connect(DB_PATH) as db:
        if user_id:
            await db.execute("DELETE FROM xp WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        else:
            await db.execute("DELETE FROM xp WHERE chat_id=?", (chat_id,))
        await db.commit()


async def create_giveaway(chat_id, admin_id, prize, winners, closes_at) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO giveaways (chat_id, admin_id, prize, winners, closes_at) VALUES (?,?,?,?,?)",
            (chat_id, admin_id, prize, winners, closes_at),
        )
        await db.commit()
        return cur.lastrowid


async def set_giveaway_message(gid: int, message_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE giveaways SET message_id=? WHERE id=?", (message_id, gid))
        await db.commit()


async def get_giveaway(gid: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM giveaways WHERE id=?", (gid,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def join_giveaway(gid: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO giveaway_members (giveaway_id, user_id) VALUES (?,?)",
                (gid, user_id),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def giveaway_members(gid: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_id FROM giveaway_members WHERE giveaway_id=?", (gid,)
        )
        return [r[0] for r in await cur.fetchall()]


async def close_giveaway(gid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE giveaways SET closed=1 WHERE id=?", (gid,))
        await db.commit()


async def due_giveaways(now: float) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM giveaways WHERE closed=0 AND closes_at<=?", (now,)
        )
        return [dict(r) for r in await cur.fetchall()]


async def add_alias(chat_id: int, alias: str, command: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO aliases (chat_id, alias, command) VALUES (?,?,?)
            ON CONFLICT(chat_id, alias) DO UPDATE SET command=excluded.command
            """,
            (chat_id, alias.lower().lstrip("/"), command.lower().lstrip("/")),
        )
        await db.commit()


async def get_alias(chat_id: int, alias: str) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT command FROM aliases WHERE chat_id=? AND alias=?",
            (chat_id, alias.lower().lstrip("/")),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def list_aliases(chat_id: int) -> list[tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT alias, command FROM aliases WHERE chat_id=?", (chat_id,)
        )
        return [(r[0], r[1]) for r in await cur.fetchall()]


async def del_alias(chat_id: int, alias: str) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM aliases WHERE chat_id=? AND alias=?",
            (chat_id, alias.lower().lstrip("/")),
        )
        await db.commit()
        return cur.rowcount > 0


async def put_quarantine(chat_id, user_id, until_ts, reason=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO quarantine (chat_id, user_id, until_ts, reason) VALUES (?,?,?,?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET until_ts=excluded.until_ts, reason=excluded.reason
            """,
            (chat_id, user_id, until_ts, reason),
        )
        await db.commit()


async def get_quarantine(chat_id, user_id) -> Optional[dict]:
    import time
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM quarantine WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return None
        data = dict(row)
        if data["until_ts"] and data["until_ts"] < time.time():
            await db.execute(
                "DELETE FROM quarantine WHERE chat_id=? AND user_id=?",
                (chat_id, user_id),
            )
            await db.commit()
            return None
        return data


async def clear_quarantine(chat_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM quarantine WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        await db.commit()


async def watch_user(chat_id, user_id, admin_id, note=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO watches (chat_id, user_id, admin_id, note) VALUES (?,?,?,?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET note=excluded.note, admin_id=excluded.admin_id
            """,
            (chat_id, user_id, admin_id, note),
        )
        await db.commit()


async def unwatch_user(chat_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM watches WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        await db.commit()


async def is_watched(chat_id, user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM watches WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return await cur.fetchone() is not None


async def list_watches(chat_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM watches WHERE chat_id=?", (chat_id,))
        return [dict(r) for r in await cur.fetchall()]
