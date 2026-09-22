"""Extra tables: XP, giveaways, aliases, quarantine, watches."""
from __future__ import annotations

from datetime import datetime, timezone
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
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def init_extra():
    await init_v45_tables()
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


# ==================== RANKS (TitanMod 4.0) ====================

async def get_user_rank(chat_id: int, user_id: int) -> int:
    """Return rank level 0-7. Default 0."""
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT rank_level FROM user_ranks WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def set_user_rank(
    chat_id: int, user_id: int, level: int, set_by: int | None = None, custom_title: str | None = None
) -> None:
    level = max(0, min(7, int(level)))
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO user_ranks (chat_id, user_id, rank_level, custom_title, set_by, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                rank_level=excluded.rank_level,
                custom_title=COALESCE(excluded.custom_title, user_ranks.custom_title),
                set_by=excluded.set_by,
                updated_at=excluded.updated_at
            """,
            (chat_id, user_id, level, custom_title, set_by, _now()),
        )
        await db.commit()


async def get_rank_row(chat_id: int, user_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM user_ranks WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_ranks(chat_id: int, min_level: int = 1) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM user_ranks WHERE chat_id=? AND rank_level>=? ORDER BY rank_level DESC",
            (chat_id, min_level),
        )
        return [dict(r) for r in await cur.fetchall()]


async def clear_user_rank(chat_id: int, user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM user_ranks WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        await db.commit()


# ==================== USER PREFS / CABINET ====================

async def get_user_prefs(user_id: int) -> dict:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM user_prefs WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        if row:
            return dict(row)
        return {
            "user_id": user_id,
            "lang": "ru",
            "notify_punish": 1,
            "notify_levelup": 1,
            "theme": "default",
            "menu_hint": 1,
        }


async def set_user_pref(user_id: int, key: str, value) -> None:
    allowed = {"lang", "notify_punish", "notify_levelup", "theme", "menu_hint"}
    if key not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            f"""
            INSERT INTO user_prefs (user_id, {key}, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET {key}=excluded.{key}, updated_at=excluded.updated_at
            """,
            (user_id, value, _now()),
        )
        await db.commit()


# ==================== ECONOMY ====================

async def get_balance(chat_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT balance FROM economy WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def add_coins(chat_id: int, user_id: int, amount: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO economy (chat_id, user_id, balance, total_earned)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                balance = balance + excluded.balance,
                total_earned = total_earned + CASE WHEN excluded.balance > 0 THEN excluded.balance ELSE 0 END,
                total_spent = total_spent + CASE WHEN excluded.balance < 0 THEN -excluded.balance ELSE 0 END
            """,
            (chat_id, user_id, amount, max(0, amount)),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT balance FROM economy WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def claim_daily(chat_id: int, user_id: int, reward: int = 50) -> tuple[bool, int, int]:
    """Returns (success, new_balance, streak)."""
    from datetime import date
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM economy WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        if row and row["last_daily"] == today:
            return False, int(row["balance"]), int(row["streak"] or 0)
        streak = 1
        if row and row["last_daily"]:
            try:
                from datetime import datetime, timezone as dt
                last = dt.fromisoformat(row["last_daily"]).date()
                if (date.today() - last).days == 1:
                    streak = int(row["streak"] or 0) + 1
            except Exception:
                pass
        bonus = min(streak * 5, 50)
        total = reward + bonus
        await db.execute(
            """
            INSERT INTO economy (chat_id, user_id, balance, total_earned, last_daily, streak)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET
                balance = balance + ?,
                total_earned = total_earned + ?,
                last_daily = ?,
                streak = ?
            """,
            (chat_id, user_id, total, total, today, streak, total, total, today, streak),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT balance FROM economy WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        bal = await cur.fetchone()
        return True, int(bal[0]) if bal else total, streak


async def economy_top(chat_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM economy WHERE chat_id=? ORDER BY balance DESC LIMIT ?",
            (chat_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


# ==================== TICKETS ====================

async def create_ticket(user_id: int, subject: str, chat_id: int | None = None, first_message: str = "") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO tickets (chat_id, user_id, status, subject) VALUES (?, ?, 'open', ?)",
            (chat_id, user_id, subject),
        )
        await db.commit()
        tid = cur.lastrowid
        if first_message:
            await db.execute(
                "INSERT INTO ticket_messages (ticket_id, user_id, text) VALUES (?, ?, ?)",
                (tid, user_id, first_message),
            )
            await db.commit()
        return int(tid)


async def add_ticket_message(ticket_id: int, user_id: int, text: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO ticket_messages (ticket_id, user_id, text) VALUES (?, ?, ?)",
            (ticket_id, user_id, text),
        )
        await db.commit()


async def get_ticket(ticket_id: int) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM tickets WHERE id=?", (ticket_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_tickets(user_id: int | None = None, status: str | None = None, limit: int = 30) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        q = "SELECT * FROM tickets WHERE 1=1"
        args: list = []
        if user_id is not None:
            q += " AND user_id=?"
            args.append(user_id)
        if status is not None:
            q += " AND status=?"
            args.append(status)
        q += " ORDER BY id DESC LIMIT ?"
        args.append(limit)
        cur = await db.execute(q, args)
        return [dict(r) for r in await cur.fetchall()]


async def close_ticket(ticket_id: int, closed_by: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE tickets SET status='closed', closed_at=?, closed_by=? WHERE id=?",
            (_now(), closed_by, ticket_id),
        )
        await db.commit()


async def list_ticket_messages(ticket_id: int, limit: int = 50) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM ticket_messages WHERE ticket_id=? ORDER BY id ASC LIMIT ?",
            (ticket_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]



# ==================== ECONOMY COOLDOWNS ====================

async def _ensure_cd_table(db):
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS economy_cd (
            chat_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            last_ts REAL NOT NULL DEFAULT 0,
            PRIMARY KEY (chat_id, user_id, action)
        )
        """
    )


async def check_cooldown(chat_id: int, user_id: int, action: str, seconds: int) -> tuple[bool, int]:
    """Returns (allowed, seconds_left)."""
    import time
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_cd_table(db)
        cur = await db.execute(
            "SELECT last_ts FROM economy_cd WHERE chat_id=? AND user_id=? AND action=?",
            (chat_id, user_id, action),
        )
        row = await cur.fetchone()
        if row:
            left = int(seconds - (now - float(row[0])))
            if left > 0:
                return False, left
        return True, 0


async def set_cooldown(chat_id: int, user_id: int, action: str) -> None:
    import time
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        await _ensure_cd_table(db)
        await db.execute(
            """
            INSERT INTO economy_cd (chat_id, user_id, action, last_ts) VALUES (?, ?, ?, ?)
            ON CONFLICT(chat_id, user_id, action) DO UPDATE SET last_ts=excluded.last_ts
            """,
            (chat_id, user_id, action, now),
        )
        await db.commit()


# ==================== v4.5 TABLES ====================

async def init_v45_tables():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript(
            """
            CREATE TABLE IF NOT EXISTS inventory (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                item TEXT NOT NULL,
                qty INTEGER DEFAULT 1,
                expires_at REAL DEFAULT 0,
                PRIMARY KEY (chat_id, user_id, item)
            );
            CREATE TABLE IF NOT EXISTS reputation (
                chat_id INTEGER NOT NULL,
                from_id INTEGER NOT NULL,
                to_id INTEGER NOT NULL,
                day TEXT NOT NULL,
                value INTEGER NOT NULL,
                PRIMARY KEY (chat_id, from_id, to_id, day)
            );
            CREATE TABLE IF NOT EXISTS rep_scores (
                chat_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                score INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, user_id)
            );
            CREATE TABLE IF NOT EXISTS marriages (
                chat_id INTEGER NOT NULL,
                user_a INTEGER NOT NULL,
                user_b INTEGER NOT NULL,
                since TEXT,
                PRIMARY KEY (chat_id, user_a, user_b)
            );
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id INTEGER NOT NULL,
                admin_id INTEGER,
                text TEXT NOT NULL,
                run_at REAL NOT NULL,
                done INTEGER DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS mod_stats (
                chat_id INTEGER NOT NULL,
                admin_id INTEGER NOT NULL,
                action TEXT NOT NULL,
                cnt INTEGER DEFAULT 0,
                PRIMARY KEY (chat_id, admin_id, action)
            );
            """
        )
        await db.commit()


async def inv_add(chat_id: int, user_id: int, item: str, qty: int = 1, expires_at: float = 0) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO inventory (chat_id, user_id, item, qty, expires_at) VALUES (?,?,?,?,?)
            ON CONFLICT(chat_id, user_id, item) DO UPDATE SET
                qty = qty + excluded.qty,
                expires_at = CASE WHEN excluded.expires_at > inventory.expires_at
                    THEN excluded.expires_at ELSE inventory.expires_at END
            """,
            (chat_id, user_id, item, qty, expires_at),
        )
        await db.commit()


async def inv_list(chat_id: int, user_id: int) -> list[dict]:
    import time
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM inventory WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        rows = [dict(r) for r in await cur.fetchall()]
    out = []
    for r in rows:
        exp = float(r.get("expires_at") or 0)
        if exp and exp < now:
            continue
        out.append(r)
    return out


async def inv_has(chat_id: int, user_id: int, item: str) -> bool:
    items = await inv_list(chat_id, user_id)
    return any(i["item"] == item and int(i.get("qty") or 0) > 0 for i in items)


async def rep_vote(chat_id: int, from_id: int, to_id: int, value: int) -> tuple[bool, str, int]:
    from datetime import date
    if from_id == to_id:
        return False, "Нельзя себе", 0
    if value not in (1, -1):
        return False, "Только +1 или -1", 0
    day = date.today().isoformat()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM reputation WHERE chat_id=? AND from_id=? AND to_id=? AND day=?",
            (chat_id, from_id, to_id, day),
        )
        if await cur.fetchone():
            return False, "Уже голосовали за этого сегодня", 0
        await db.execute(
            "INSERT INTO reputation (chat_id, from_id, to_id, day, value) VALUES (?,?,?,?,?)",
            (chat_id, from_id, to_id, day, value),
        )
        await db.execute(
            """
            INSERT INTO rep_scores (chat_id, user_id, score) VALUES (?,?,?)
            ON CONFLICT(chat_id, user_id) DO UPDATE SET score = score + excluded.score
            """,
            (chat_id, to_id, value),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT score FROM rep_scores WHERE chat_id=? AND user_id=?",
            (chat_id, to_id),
        )
        row = await cur.fetchone()
        return True, "ok", int(row[0]) if row else value


async def rep_get(chat_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT score FROM rep_scores WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return int(row[0]) if row else 0


async def rep_top(chat_id: int, limit: int = 10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM rep_scores WHERE chat_id=? ORDER BY score DESC LIMIT ?",
            (chat_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def marry(chat_id: int, a: int, b: int) -> bool:
    if a == b:
        return False
    a, b = min(a, b), max(a, b)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO marriages (chat_id, user_a, user_b, since) VALUES (?,?,?,?)",
            (chat_id, a, b, _now()),
        )
        await db.commit()
    return True


async def divorce(chat_id: int, user_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM marriages WHERE chat_id=? AND (user_a=? OR user_b=?)",
            (chat_id, user_id, user_id),
        )
        await db.commit()
        return cur.rowcount > 0


async def get_spouse(chat_id: int, user_id: int) -> int | None:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT user_a, user_b FROM marriages WHERE chat_id=? AND (user_a=? OR user_b=?)",
            (chat_id, user_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            return None
        return int(row[1] if int(row[0]) == user_id else row[0])


async def schedule_post(chat_id: int, admin_id: int, text: str, run_at: float) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO scheduled_posts (chat_id, admin_id, text, run_at) VALUES (?,?,?,?)",
            (chat_id, admin_id, text, run_at),
        )
        await db.commit()
        return int(cur.lastrowid)


async def due_scheduled(now: float) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM scheduled_posts WHERE done=0 AND run_at<=? ORDER BY id LIMIT 20",
            (now,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def mark_scheduled_done(pid: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE scheduled_posts SET done=1 WHERE id=?", (pid,))
        await db.commit()


async def bump_mod_stat(chat_id: int, admin_id: int, action: str) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO mod_stats (chat_id, admin_id, action, cnt) VALUES (?,?,?,1)
            ON CONFLICT(chat_id, admin_id, action) DO UPDATE SET cnt = cnt + 1
            """,
            (chat_id, admin_id, action),
        )
        await db.commit()


async def mod_stats_top(chat_id: int, limit: int = 15) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT admin_id, SUM(cnt) AS total FROM mod_stats
            WHERE chat_id=? GROUP BY admin_id ORDER BY total DESC LIMIT ?
            """,
            (chat_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]
