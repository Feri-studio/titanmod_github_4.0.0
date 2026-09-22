import json
import os
import time
from datetime import datetime, timezone
from typing import Any, Optional

import aiosqlite

from config import config
from core.defaults import DEFAULT_SETTINGS
from database.schema import SCHEMA


def _resolve_db_path() -> str:
    raw = os.getenv("DB_PATH") or config.DB_PATH or "data/moderation_bot.db"
    path = os.path.abspath(raw)
    folder = os.path.dirname(path)
    if folder:
        os.makedirs(folder, exist_ok=True)
    return path


DB_PATH = _resolve_db_path()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _durable_commit(db) -> None:
    """Commit and hint WAL to flush to the main DB file."""
    await db.commit()
    try:
        await db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    except Exception:
        try:
            await db.execute("PRAGMA wal_checkpoint(PASSIVE)")
        except Exception:
            pass


def _merge_settings(raw: Any) -> dict:
    data = {}
    if isinstance(raw, dict):
        data = raw
    elif isinstance(raw, str) and raw:
        try:
            data = json.loads(raw)
        except Exception:
            data = {}
    merged = dict(DEFAULT_SETTINGS)
    merged.update(data or {})
    return merged


async def init_db():
    global DB_PATH
    DB_PATH = _resolve_db_path()
    # keep extra module on the same file
    try:
        import database.extra as extra_mod
        extra_mod.DB_PATH = DB_PATH
    except Exception:
        pass
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL")
        await db.execute("PRAGMA synchronous=NORMAL")
        await db.execute("PRAGMA foreign_keys=ON")
        await db.execute("PRAGMA busy_timeout=5000")
        for stmt in SCHEMA:
            await db.execute(stmt)
        await _durable_commit(db)
    from database.extra import init_extra
    await init_extra()
    await migrate_chat_settings()


async def migrate_chat_settings():
    """Merge DEFAULT_SETTINGS into every chat so new keys appear after upgrades."""
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT chat_id, settings FROM chats")
        rows = await cur.fetchall()
        for row in rows:
            merged = _merge_settings(row["settings"])
            await db.execute(
                "UPDATE chats SET settings=?, updated_at=? WHERE chat_id=?",
                (json.dumps(merged, ensure_ascii=False), _now(), row["chat_id"]),
            )
        await db.commit()


async def _conn():
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    return db


# ==================== USERS / CHATS ====================

async def upsert_user(user) -> None:
    if not user:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO users (user_id, username, first_name, last_name, is_bot, last_seen)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                last_seen=excluded.last_seen
            """,
            (
                user.id,
                getattr(user, "username", None),
                getattr(user, "first_name", None),
                getattr(user, "last_name", None),
                1 if getattr(user, "is_bot", False) else 0,
                _now(),
            ),
        )
        await db.commit()


async def get_user(user_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def add_name_history(user) -> None:
    if not user:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT name, username FROM name_history WHERE user_id=? ORDER BY id DESC LIMIT 1",
            (user.id,),
        )
        row = await cur.fetchone()
        name = getattr(user, "full_name", None) or getattr(user, "first_name", None)
        uname = getattr(user, "username", None)
        if row and row[0] == name and row[1] == uname:
            return
        await db.execute(
            "INSERT INTO name_history (user_id, name, username) VALUES (?, ?, ?)",
            (user.id, name, uname),
        )
        await db.commit()


async def get_name_history(user_id: int, limit: int = 15) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM name_history WHERE user_id=? ORDER BY id DESC LIMIT ?",
            (user_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


async def ensure_chat(chat_id: int, title: str = None, chat_type: str = None, username: str = None) -> dict:
    chat = await get_chat(chat_id)
    if chat:
        if title and title != chat.get("title"):
            await update_chat_meta(chat_id, title=title, chat_type=chat_type, username=username)
            chat["title"] = title
        return chat
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO chats (chat_id, title, chat_type, username, settings) VALUES (?, ?, ?, ?, ?)",
            (chat_id, title or "Unknown", chat_type, username, json.dumps(DEFAULT_SETTINGS, ensure_ascii=False)),
        )
        await db.execute("INSERT OR IGNORE INTO bot_chats (chat_id) VALUES (?)", (chat_id,))
        await db.commit()
    return await get_chat(chat_id)


async def get_chat(chat_id: int) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM chats WHERE chat_id=?", (chat_id,))
        row = await cur.fetchone()
        if not row:
            return None
        data = dict(row)
        data["settings"] = _merge_settings(data.get("settings"))
        return data


async def get_settings(chat_id: int) -> dict:
    chat = await get_chat(chat_id)
    if not chat:
        return dict(DEFAULT_SETTINGS)
    return chat["settings"]


async def update_chat_meta(chat_id: int, **kwargs):
    if not kwargs:
        return
    kwargs["updated_at"] = _now()
    keys = ", ".join(f"{k}=?" for k in kwargs)
    values = list(kwargs.values()) + [chat_id]
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(f"UPDATE chats SET {keys} WHERE chat_id=?", values)
        await db.commit()


async def update_settings(chat_id: int, **kwargs):
    """Persist chat settings. Always ensures the chat row exists."""
    await ensure_chat(chat_id)
    settings = await get_settings(chat_id)
    settings.update(kwargs)
    payload = json.dumps(settings, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "UPDATE chats SET settings=?, updated_at=? WHERE chat_id=?",
            (payload, _now(), chat_id),
        )
        if cur.rowcount == 0:
            # Race: chat disappeared — insert fresh
            await db.execute(
                "INSERT INTO chats (chat_id, title, settings) VALUES (?, ?, ?)",
                (chat_id, "Unknown", payload),
            )
        await _durable_commit(db)
    return settings


async def reset_settings(chat_id: int):
    await ensure_chat(chat_id)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE chats SET settings=?, updated_at=? WHERE chat_id=?",
            (json.dumps(DEFAULT_SETTINGS, ensure_ascii=False), _now(), chat_id),
        )
        await db.commit()


async def list_chats() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT chat_id, title, username, chat_type FROM chats")
        return [dict(r) for r in await cur.fetchall()]


async def count_chats() -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT COUNT(*) FROM chats")
        return (await cur.fetchone())[0]


# ==================== WARNS ====================

async def add_warn(chat_id: int, user_id: int, admin_id: int, reason: str = "Без причины") -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO warns (chat_id, user_id, admin_id, reason) VALUES (?, ?, ?, ?)",
            (chat_id, user_id, admin_id, reason),
        )
        await db.commit()
        cur = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return (await cur.fetchone())[0]


async def remove_warn(chat_id: int, user_id: int, count: int = 1) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT id FROM warns WHERE chat_id=? AND user_id=? ORDER BY created_at DESC LIMIT ?",
            (chat_id, user_id, count),
        )
        ids = [r[0] for r in await cur.fetchall()]
        if ids:
            q = ",".join("?" * len(ids))
            await db.execute(f"DELETE FROM warns WHERE id IN ({q})", ids)
            await db.commit()
        cur = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return (await cur.fetchone())[0]


async def get_warns(chat_id: int, user_id: int) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM warns WHERE chat_id=? AND user_id=? ORDER BY created_at DESC",
            (chat_id, user_id),
        )
        return [dict(r) for r in await cur.fetchall()]


async def get_warns_count(chat_id: int, user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT COUNT(*) FROM warns WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return (await cur.fetchone())[0]


async def clear_warns(chat_id: int, user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM warns WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        await db.commit()


# ==================== PUNISHMENTS ====================

async def add_punishment(chat_id, user_id, admin_id, ptype, reason="", until_date=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO punishments (chat_id, user_id, admin_id, type, reason, until_date) VALUES (?,?,?,?,?,?)",
            (chat_id, user_id, admin_id, ptype, reason, until_date),
        )
        await db.commit()


async def get_punishments(chat_id: int, user_id: int, limit: int = 20) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM punishments WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, user_id, limit),
        )
        return [dict(r) for r in await cur.fetchall()]


# ==================== NOTES ====================

async def save_note(chat_id, name, content, admin_id, file_id=None, file_type=None, buttons=None):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO notes (chat_id, name, content, file_id, file_type, buttons, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, name) DO UPDATE SET
                content=excluded.content, file_id=excluded.file_id, file_type=excluded.file_type,
                buttons=excluded.buttons, admin_id=excluded.admin_id
            """,
            (chat_id, name.lower(), content, file_id, file_type, buttons, admin_id),
        )
        await db.commit()


async def get_note(chat_id, name) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM notes WHERE chat_id=? AND name=?",
            (chat_id, name.lower()),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_notes(chat_id) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT name FROM notes WHERE chat_id=? ORDER BY name", (chat_id,))
        return [r[0] for r in await cur.fetchall()]


async def delete_note(chat_id, name) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM notes WHERE chat_id=? AND name=?", (chat_id, name.lower()))
        await db.commit()
        return cur.rowcount > 0


async def clear_notes(chat_id) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM notes WHERE chat_id=?", (chat_id,))
        await db.commit()
        return cur.rowcount


# ==================== FILTERS ====================

async def save_filter(chat_id, keyword, content, admin_id, file_id=None, file_type=None, buttons=None, exact=0):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO filters (chat_id, keyword, content, file_id, file_type, buttons, exact, admin_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(chat_id, keyword) DO UPDATE SET
                content=excluded.content, file_id=excluded.file_id, file_type=excluded.file_type,
                buttons=excluded.buttons, exact=excluded.exact, admin_id=excluded.admin_id
            """,
            (chat_id, keyword.lower(), content, file_id, file_type, buttons, exact, admin_id),
        )
        await db.commit()


async def get_filters(chat_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM filters WHERE chat_id=?", (chat_id,))
        return [dict(r) for r in await cur.fetchall()]


async def delete_filter(chat_id, keyword) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM filters WHERE chat_id=? AND keyword=?", (chat_id, keyword.lower()))
        await db.commit()
        return cur.rowcount > 0


async def clear_filters(chat_id) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM filters WHERE chat_id=?", (chat_id,))
        await db.commit()
        return cur.rowcount


async def bump_filter_use(fid: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE filters SET uses=uses+1 WHERE id=?", (fid,))
        await db.commit()


# ==================== WORDS / LINKS / USERS ====================

async def add_badword(chat_id, word) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute("INSERT INTO badwords (chat_id, word) VALUES (?, ?)", (chat_id, word.lower()))
            await db.commit()
            return True
        except Exception:
            return False


async def remove_badword(chat_id, word):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM badwords WHERE chat_id=? AND word=?", (chat_id, word.lower()))
        await db.commit()


async def get_badwords(chat_id) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT word FROM badwords WHERE chat_id=?", (chat_id,))
        return [r[0] for r in await cur.fetchall()]


async def add_whitelist(chat_id, domain) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        try:
            await db.execute(
                "INSERT INTO whitelist_links (chat_id, domain) VALUES (?, ?)",
                (chat_id, domain.lower()),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def remove_whitelist(chat_id, domain):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM whitelist_links WHERE chat_id=? AND domain=?", (chat_id, domain.lower()))
        await db.commit()


async def get_whitelist(chat_id) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT domain FROM whitelist_links WHERE chat_id=?", (chat_id,))
        return [r[0] for r in await cur.fetchall()]


async def approve_user(chat_id, user_id, admin_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO approved (chat_id, user_id, admin_id) VALUES (?, ?, ?)",
            (chat_id, user_id, admin_id),
        )
        await db.commit()


async def unapprove_user(chat_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM approved WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        await db.commit()


async def is_approved(chat_id, user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM approved WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        return await cur.fetchone() is not None


async def list_approved(chat_id) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM approved WHERE chat_id=?", (chat_id,))
        return [r[0] for r in await cur.fetchall()]


# ==================== FEDERATION ====================

async def create_fed(fed_id, owner_id, name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO federations (fed_id, owner_id, name) VALUES (?, ?, ?)",
            (fed_id, owner_id, name),
        )
        await db.execute("INSERT INTO fed_admins (fed_id, user_id) VALUES (?, ?)", (fed_id, owner_id))
        await db.commit()


async def delete_fed(fed_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM federations WHERE fed_id=?", (fed_id,))
        await db.execute("DELETE FROM fed_chats WHERE fed_id=?", (fed_id,))
        await db.execute("DELETE FROM fed_admins WHERE fed_id=?", (fed_id,))
        await db.execute("DELETE FROM fed_bans WHERE fed_id=?", (fed_id,))
        await db.commit()


async def get_fed(fed_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM federations WHERE fed_id=?", (fed_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def get_fed_by_owner(owner_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM federations WHERE owner_id=?", (owner_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def join_fed(fed_id, chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO fed_chats (fed_id, chat_id) VALUES (?, ?)", (fed_id, chat_id))
        await db.commit()


async def leave_fed(fed_id, chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM fed_chats WHERE fed_id=? AND chat_id=?", (fed_id, chat_id))
        await db.commit()


async def get_chat_fed(chat_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            """
            SELECT f.* FROM federations f
            JOIN fed_chats c ON c.fed_id=f.fed_id
            WHERE c.chat_id=?
            """,
            (chat_id,),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def fed_ban(fed_id, user_id, admin_id, reason):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO fed_bans (fed_id, user_id, admin_id, reason) VALUES (?, ?, ?, ?)
            ON CONFLICT(fed_id, user_id) DO UPDATE SET reason=excluded.reason, admin_id=excluded.admin_id
            """,
            (fed_id, user_id, admin_id, reason),
        )
        await db.commit()


async def fed_unban(fed_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM fed_bans WHERE fed_id=? AND user_id=?", (fed_id, user_id))
        await db.commit()


async def is_fbanned(fed_id, user_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM fed_bans WHERE fed_id=? AND user_id=?",
            (fed_id, user_id),
        )
        row = await cur.fetchone()
        return dict(row) if row else None


async def fed_chats(fed_id) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT chat_id FROM fed_chats WHERE fed_id=?", (fed_id,))
        return [r[0] for r in await cur.fetchall()]


async def fed_admins(fed_id) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT user_id FROM fed_admins WHERE fed_id=?", (fed_id,))
        return [r[0] for r in await cur.fetchall()]


async def fpromote(fed_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT OR IGNORE INTO fed_admins (fed_id, user_id) VALUES (?, ?)", (fed_id, user_id))
        await db.commit()


async def fdemote(fed_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM fed_admins WHERE fed_id=? AND user_id=?", (fed_id, user_id))
        await db.commit()


async def list_fbans(fed_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM fed_bans WHERE fed_id=?", (fed_id,))
        return [dict(r) for r in await cur.fetchall()]


# ==================== GBANS ====================

async def gban_user(user_id, admin_id, reason):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO gbans (user_id, admin_id, reason) VALUES (?, ?, ?)",
            (user_id, admin_id, reason),
        )
        await db.execute("UPDATE users SET gbanned=1, gban_reason=? WHERE user_id=?", (reason, user_id))
        await db.commit()


async def ungban_user(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM gbans WHERE user_id=?", (user_id,))
        await db.execute("UPDATE users SET gbanned=0, gban_reason=NULL WHERE user_id=?", (user_id,))
        await db.commit()


async def is_gbanned(user_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM gbans WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def list_gbans() -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM gbans")
        return [dict(r) for r in await cur.fetchall()]


# ==================== CONNECTIONS ====================

async def connect_chat(user_id, chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO connections (user_id, chat_id) VALUES (?, ?)",
            (user_id, chat_id),
        )
        await db.commit()


async def disconnect_chat(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM connections WHERE user_id=?", (user_id,))
        await db.commit()


async def get_connection(user_id) -> Optional[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT chat_id FROM connections WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return row[0] if row else None


# ==================== CAPTCHA / FLOOD / JOIN ====================

async def set_captcha(chat_id, user_id, answer, message_id, expires):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO captcha (chat_id, user_id, answer, message_id, expires) VALUES (?,?,?,?,?)",
            (chat_id, user_id, str(answer), message_id, expires),
        )
        await db.commit()


async def get_captcha(chat_id, user_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM captcha WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        row = await cur.fetchone()
        return dict(row) if row else None


async def del_captcha(chat_id, user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM captcha WHERE chat_id=? AND user_id=?", (chat_id, user_id))
        await db.commit()


async def expired_captchas(now: float) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM captcha WHERE expires < ?", (now,))
        return [dict(r) for r in await cur.fetchall()]


async def check_flood(chat_id, user_id, limit, period, text="") -> tuple[bool, int]:
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT message_count, first_message_time, last_text, dup_count FROM flood_tracker WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        if not row:
            await db.execute(
                "INSERT INTO flood_tracker (chat_id, user_id, message_count, first_message_time, last_text, dup_count) VALUES (?,?,1,?,?,0)",
                (chat_id, user_id, now, text or ""),
            )
            await db.commit()
            return False, 1
        count, first, last_text, dups = row
        if now - (first or now) > period:
            await db.execute(
                "UPDATE flood_tracker SET message_count=1, first_message_time=?, last_text=?, dup_count=0 WHERE chat_id=? AND user_id=?",
                (now, text or "", chat_id, user_id),
            )
            await db.commit()
            return False, 1
        new_count = (count or 0) + 1
        dup = (dups or 0) + 1 if (text and text == last_text) else 0
        await db.execute(
            "UPDATE flood_tracker SET message_count=?, last_text=?, dup_count=? WHERE chat_id=? AND user_id=?",
            (new_count, text or last_text, dup, chat_id, user_id),
        )
        await db.commit()
        return new_count > limit, new_count


async def get_dup_count(chat_id, user_id) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT dup_count FROM flood_tracker WHERE chat_id=? AND user_id=?",
            (chat_id, user_id),
        )
        row = await cur.fetchone()
        return row[0] if row else 0


async def track_join(chat_id, window: int) -> int:
    now = time.time()
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT joins, window_start FROM join_tracker WHERE chat_id=?", (chat_id,))
        row = await cur.fetchone()
        if not row or now - (row[1] or 0) > window:
            await db.execute(
                "INSERT OR REPLACE INTO join_tracker (chat_id, joins, window_start) VALUES (?, 1, ?)",
                (chat_id, now),
            )
            await db.commit()
            return 1
        joins = (row[0] or 0) + 1
        await db.execute("UPDATE join_tracker SET joins=? WHERE chat_id=?", (joins, chat_id))
        await db.commit()
        return joins


# ==================== STATS / LOGS ====================

async def bump_stat(chat_id, field: str, amount: int = 1):
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    allowed = {"messages", "joins", "leaves", "warns", "bans", "mutes", "kicks", "deleted"}
    if field not in allowed:
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO stats (chat_id, date) VALUES (?, ?)",
            (chat_id, date),
        )
        await db.execute(
            f"UPDATE stats SET {field}={field}+? WHERE chat_id=? AND date=?",
            (amount, chat_id, date),
        )
        await db.commit()


async def get_stats(chat_id, days: int = 7) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM stats WHERE chat_id=? ORDER BY date DESC LIMIT ?",
            (chat_id, days),
        )
        return [dict(r) for r in await cur.fetchall()]


async def add_event(chat_id, event, user_id=None, admin_id=None, payload=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO event_log (chat_id, user_id, admin_id, event, payload) VALUES (?,?,?,?,?)",
            (chat_id, user_id, admin_id, event, payload[:2000] if payload else ""),
        )
        await db.commit()


async def add_report(chat_id, user_id, target_id, message_id, reason):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reports (chat_id, user_id, target_id, message_id, reason) VALUES (?,?,?,?,?)",
            (chat_id, user_id, target_id, message_id, reason),
        )
        await db.commit()


async def add_user_note(chat_id, user_id, admin_id, note):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO user_notes (chat_id, user_id, admin_id, note) VALUES (?,?,?,?)",
            (chat_id, user_id, admin_id, note),
        )
        await db.commit()


async def get_user_notes(chat_id, user_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT * FROM user_notes WHERE chat_id=? AND user_id=? ORDER BY id DESC",
            (chat_id, user_id),
        )
        return [dict(r) for r in await cur.fetchall()]


# ==================== REP / AFK / REMINDERS ====================

async def change_rep(chat_id, from_id, to_id, delta) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO reputation_log (chat_id, from_id, to_id, delta) VALUES (?,?,?,?)",
            (chat_id, from_id, to_id, delta),
        )
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, reputation) VALUES (?, 0)",
            (to_id,),
        )
        await db.execute("UPDATE users SET reputation=reputation+? WHERE user_id=?", (delta, to_id))
        await db.commit()
        cur = await db.execute("SELECT reputation FROM users WHERE user_id=?", (to_id,))
        row = await cur.fetchone()
        return row[0] if row else delta


async def last_rep_time(chat_id, from_id, to_id) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT created_at FROM reputation_log WHERE chat_id=? AND from_id=? AND to_id=? ORDER BY id DESC LIMIT 1",
            (chat_id, from_id, to_id),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def top_rep(limit=10) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(
            "SELECT user_id, first_name, username, reputation FROM users ORDER BY reputation DESC LIMIT ?",
            (limit,),
        )
        return [dict(r) for r in await cur.fetchall()]


async def set_afk(user_id, reason):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO afk (user_id, reason, since) VALUES (?, ?, ?)",
            (user_id, reason, _now()),
        )
        await db.commit()


async def get_afk(user_id) -> Optional[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM afk WHERE user_id=?", (user_id,))
        row = await cur.fetchone()
        return dict(row) if row else None


async def clear_afk(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM afk WHERE user_id=?", (user_id,))
        await db.commit()


async def add_reminder(chat_id, user_id, text, fire_at) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "INSERT INTO reminders (chat_id, user_id, text, fire_at) VALUES (?,?,?,?)",
            (chat_id, user_id, text, fire_at),
        )
        await db.commit()
        return cur.lastrowid


async def due_reminders(now: float) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM reminders WHERE fire_at <= ?", (now,))
        rows = [dict(r) for r in await cur.fetchall()]
        if rows:
            ids = [r["id"] for r in rows]
            q = ",".join("?" * len(ids))
            await db.execute(f"DELETE FROM reminders WHERE id IN ({q})", ids)
            await db.commit()
        return rows


async def list_reminders(user_id) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM reminders WHERE user_id=? ORDER BY fire_at", (user_id,))
        return [dict(r) for r in await cur.fetchall()]


async def delete_reminder(rid, user_id) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("DELETE FROM reminders WHERE id=? AND user_id=?", (rid, user_id))
        await db.commit()
        return cur.rowcount > 0


# ==================== DISABLE / CUSTOM ====================

async def disable_command(chat_id, command):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO disabled_commands (chat_id, command) VALUES (?, ?)",
            (chat_id, command.lower()),
        )
        await db.commit()


async def enable_command(chat_id, command):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM disabled_commands WHERE chat_id=? AND command=?",
            (chat_id, command.lower()),
        )
        await db.commit()


async def is_disabled(chat_id, command) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM disabled_commands WHERE chat_id=? AND command=?",
            (chat_id, command.lower()),
        )
        return await cur.fetchone() is not None


async def list_disabled(chat_id) -> list[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT command FROM disabled_commands WHERE chat_id=?", (chat_id,))
        return [r[0] for r in await cur.fetchall()]


async def set_custom_command(chat_id, command, content):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO custom_commands (chat_id, command, content) VALUES (?, ?, ?)",
            (chat_id, command.lower(), content),
        )
        await db.commit()


async def get_custom_command(chat_id, command) -> Optional[str]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT content FROM custom_commands WHERE chat_id=? AND command=?",
            (chat_id, command.lower()),
        )
        row = await cur.fetchone()
        return row[0] if row else None


async def list_custom_commands(chat_id) -> list[tuple[str, str]]:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute("SELECT command, content FROM custom_commands WHERE chat_id=?", (chat_id,))
        return [(r[0], r[1]) for r in await cur.fetchall()]


async def delete_custom_command(chat_id, command) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "DELETE FROM custom_commands WHERE chat_id=? AND command=?",
            (chat_id, command.lower()),
        )
        await db.commit()
        return cur.rowcount > 0


# ==================== STICKERS ====================

async def add_bl_sticker(chat_id, unique, pack=""):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO blacklist_stickers (chat_id, file_unique, pack) VALUES (?, ?, ?)",
            (chat_id, unique, pack or ""),
        )
        await db.commit()


async def is_bl_sticker(chat_id, unique) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(
            "SELECT 1 FROM blacklist_stickers WHERE chat_id=? AND file_unique=?",
            (chat_id, unique),
        )
        return await cur.fetchone() is not None


async def export_chat(chat_id) -> dict:
    chat = await get_chat(chat_id)
    return {
        "chat": {"chat_id": chat_id, "title": chat.get("title") if chat else None},
        "settings": await get_settings(chat_id),
        "notes": [{"name": n, **((await get_note(chat_id, n)) or {})} for n in await list_notes(chat_id)],
        "filters": await get_filters(chat_id),
        "badwords": await get_badwords(chat_id),
        "whitelist": await get_whitelist(chat_id),
        "disabled": await list_disabled(chat_id),
        "approved": await list_approved(chat_id),
    }
