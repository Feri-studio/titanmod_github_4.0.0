"""SQLite access for TitanMod web panel."""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from config import config


def _connect() -> sqlite3.Connection:
    path = Path(config.DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:
        pass
    return conn


def q(sql: str, args: tuple = ()) -> list[dict[str, Any]]:
    try:
        with _connect() as conn:
            cur = conn.execute(sql, args)
            return [dict(r) for r in cur.fetchall()]
    except Exception:
        return []


def q1(sql: str, args: tuple = ()) -> dict[str, Any] | None:
    rows = q(sql, args)
    return rows[0] if rows else None


def execute(sql: str, args: tuple = ()) -> bool:
    try:
        with _connect() as conn:
            conn.execute(sql, args)
            conn.commit()
        return True
    except Exception:
        return False


def table_exists(name: str) -> bool:
    return bool(q1("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)))


def list_tables() -> list[str]:
    return [r["name"] for r in q("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]


def list_chats(limit: int = 500) -> list[dict]:
    return q(
        "SELECT chat_id, title, chat_type, username, members, settings, updated_at "
        "FROM chats ORDER BY updated_at DESC LIMIT ?",
        (limit,),
    )


def get_chat(chat_id: int) -> dict | None:
    return q1("SELECT * FROM chats WHERE chat_id=?", (chat_id,))


def parse_settings(raw: str | None) -> dict:
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}


def save_settings(chat_id: int, settings: dict) -> None:
    execute(
        "UPDATE chats SET settings=?, updated_at=CURRENT_TIMESTAMP WHERE chat_id=?",
        (json.dumps(settings, ensure_ascii=False), chat_id),
    )


def patch_setting(chat_id: int, key: str, value: Any) -> None:
    chat = get_chat(chat_id)
    if not chat:
        return
    s = parse_settings(chat.get("settings"))
    s[key] = value
    save_settings(chat_id, s)


def list_warns(chat_id: int | None = None, user_id: int | None = None, limit: int = 200) -> list[dict]:
    if chat_id is not None and user_id is not None:
        return q(
            "SELECT * FROM warns WHERE chat_id=? AND user_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, user_id, limit),
        )
    if chat_id is not None:
        return q("SELECT * FROM warns WHERE chat_id=? ORDER BY id DESC LIMIT ?", (chat_id, limit))
    if user_id is not None:
        return q("SELECT * FROM warns WHERE user_id=? ORDER BY id DESC LIMIT ?", (user_id, limit))
    return q("SELECT * FROM warns ORDER BY id DESC LIMIT ?", (limit,))


def delete_warn(warn_id: int) -> bool:
    return execute("DELETE FROM warns WHERE id=?", (warn_id,))


def list_punishments(chat_id: int | None = None, limit: int = 200) -> list[dict]:
    if chat_id is not None:
        return q(
            "SELECT * FROM punishments WHERE chat_id=? ORDER BY id DESC LIMIT ?",
            (chat_id, limit),
        )
    return q("SELECT * FROM punishments ORDER BY id DESC LIMIT ?", (limit,))


def list_gbans(limit: int = 200) -> list[dict]:
    rows = q(
        "SELECT user_id, username, first_name, gban_reason, last_seen FROM users "
        "WHERE gbanned=1 ORDER BY user_id DESC LIMIT ?",
        (limit,),
    )
    if rows:
        return rows
    return q("SELECT * FROM gbans ORDER BY rowid DESC LIMIT ?", (limit,))


def un_gban(user_id: int) -> bool:
    ok = execute("UPDATE users SET gbanned=0, gban_reason=NULL WHERE user_id=?", (user_id,))
    execute("DELETE FROM gbans WHERE user_id=?", (user_id,))
    return ok


def set_gban(user_id: int, reason: str) -> bool:
    execute(
        "INSERT INTO users (user_id, gbanned, gban_reason) VALUES (?,?,?) "
        "ON CONFLICT(user_id) DO UPDATE SET gbanned=1, gban_reason=excluded.gban_reason",
        (user_id, 1, reason),
    )
    return True


def list_tickets(limit: int = 100) -> list[dict]:
    return q("SELECT * FROM tickets ORDER BY id DESC LIMIT ?", (limit,))


def list_economy_top(limit: int = 50) -> list[dict]:
    return q(
        "SELECT chat_id, user_id, balance, total_earned, total_spent, streak "
        "FROM economy ORDER BY balance DESC LIMIT ?",
        (limit,),
    )


def set_balance(chat_id: int, user_id: int, balance: int) -> bool:
    return execute(
        "INSERT INTO economy (chat_id, user_id, balance) VALUES (?,?,?) "
        "ON CONFLICT(chat_id, user_id) DO UPDATE SET balance=excluded.balance",
        (chat_id, user_id, balance),
    )


def list_notes(chat_id: int | None = None, limit: int = 200) -> list[dict]:
    if chat_id is not None:
        return q("SELECT * FROM notes WHERE chat_id=? ORDER BY name LIMIT ?", (chat_id, limit))
    return q("SELECT * FROM notes ORDER BY id DESC LIMIT ?", (limit,))


def list_filters(chat_id: int | None = None, limit: int = 200) -> list[dict]:
    if chat_id is not None:
        return q("SELECT * FROM filters WHERE chat_id=? ORDER BY keyword LIMIT ?", (chat_id, limit))
    return q("SELECT * FROM filters ORDER BY id DESC LIMIT ?", (limit,))


def list_badwords(chat_id: int | None = None, limit: int = 300) -> list[dict]:
    if chat_id is not None:
        return q("SELECT * FROM badwords WHERE chat_id=? ORDER BY word LIMIT ?", (chat_id, limit))
    return q("SELECT * FROM badwords ORDER BY id DESC LIMIT ?", (limit,))


def list_ranks(chat_id: int | None = None, limit: int = 200) -> list[dict]:
    if chat_id is not None:
        return q(
            "SELECT * FROM user_ranks WHERE chat_id=? ORDER BY level DESC LIMIT ?",
            (chat_id, limit),
        )
    return q("SELECT * FROM user_ranks ORDER BY level DESC LIMIT ?", (limit,))


def list_federations(limit: int = 100) -> list[dict]:
    return q("SELECT * FROM federations ORDER BY rowid DESC LIMIT ?", (limit,))


def list_fed_bans(limit: int = 200) -> list[dict]:
    return q("SELECT * FROM fed_bans ORDER BY rowid DESC LIMIT ?", (limit,))


def list_reports(limit: int = 100) -> list[dict]:
    return q("SELECT * FROM reports ORDER BY id DESC LIMIT ?", (limit,))


def list_event_log(limit: int = 150) -> list[dict]:
    return q("SELECT * FROM event_log ORDER BY rowid DESC LIMIT ?", (limit,))


def list_mod_stats(limit: int = 100) -> list[dict]:
    return q(
        "SELECT chat_id, admin_id, action, cnt FROM mod_stats ORDER BY cnt DESC LIMIT ?",
        (limit,),
    )


def list_inventory(limit: int = 100) -> list[dict]:
    return q("SELECT * FROM inventory ORDER BY rowid DESC LIMIT ?", (limit,))


def list_scheduled(limit: int = 50) -> list[dict]:
    return q(
        "SELECT * FROM scheduled_posts WHERE done=0 ORDER BY run_at LIMIT ?",
        (limit,),
    )


def list_marriages(limit: int = 50) -> list[dict]:
    return q("SELECT * FROM marriages ORDER BY rowid DESC LIMIT ?", (limit,))


def list_rep_top(limit: int = 50) -> list[dict]:
    return q(
        "SELECT chat_id, user_id, score FROM rep_scores ORDER BY score DESC LIMIT ?",
        (limit,),
    )


def list_xp_top(limit: int = 50) -> list[dict]:
    return q(
        "SELECT chat_id, user_id, xp, level, messages FROM xp ORDER BY xp DESC LIMIT ?",
        (limit,),
    )


def list_disabled(limit: int = 200) -> list[dict]:
    return q("SELECT * FROM disabled_commands ORDER BY rowid DESC LIMIT ?", (limit,))


def list_approved(limit: int = 200) -> list[dict]:
    return q("SELECT * FROM approved ORDER BY rowid DESC LIMIT ?", (limit,))


def list_quarantine(limit: int = 100) -> list[dict]:
    return q("SELECT * FROM quarantine ORDER BY rowid DESC LIMIT ?", (limit,))


def search_user(query: str) -> list[dict]:
    qstr = (query or "").strip()
    if not qstr:
        return []
    if qstr.lstrip("-").isdigit():
        uid = int(qstr)
        rows = q("SELECT * FROM users WHERE user_id=?", (uid,))
        if rows:
            return rows
        return [{"user_id": uid, "note": "нет в таблице users"}]
    like = f"%{qstr.lstrip('@')}%"
    return q(
        "SELECT * FROM users WHERE username LIKE ? OR first_name LIKE ? LIMIT 50",
        (like, like),
    )


def stats_overview() -> dict:
    def cnt(table: str) -> int:
        row = q1(f"SELECT COUNT(*) AS c FROM {table}")
        return int(row["c"]) if row else 0

    out = {}
    for t in (
        "chats", "users", "warns", "punishments", "notes", "filters", "tickets",
        "economy", "user_ranks", "reports", "federations", "badwords",
    ):
        out[t] = cnt(t) if table_exists(t) else 0
    activated = 0
    for c in list_chats(1000):
        s = parse_settings(c.get("settings"))
        if s.get("group_activated"):
            activated += 1
    out["activated_chats"] = activated
    return out
