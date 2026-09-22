"""
TitanMod 4.0 — Hierarchy / Rank system.

Ranks (from lowest to highest):
  0  member      — обычный участник
  1  trusted     — доверенный
  2  helper      — помощник
  3  moderator   — модератор
  4  senior      — старший модератор
  5  admin       — администратор
  6  head        — главный админ
  7  owner       — владелец чата / бота
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

# Rank id → metadata
RANKS: dict[int, dict] = {
    0: {
        "key": "member",
        "name_ru": "Участник",
        "name_en": "Member",
        "emoji": "👤",
        "color": "#9e9e9e",
        "perms": set(),
    },
    1: {
        "key": "trusted",
        "name_ru": "Доверенный",
        "name_en": "Trusted",
        "emoji": "⭐",
        "color": "#4caf50",
        "perms": {"bypass_locks", "bypass_flood", "bypass_captcha"},
    },
    2: {
        "key": "helper",
        "name_ru": "Помощник",
        "name_en": "Helper",
        "emoji": "🛡",
        "color": "#2196f3",
        "perms": {
            "bypass_locks", "bypass_flood", "bypass_captcha",
            "warn", "mute", "delete", "report_view", "notes_view",
        },
    },
    3: {
        "key": "moderator",
        "name_ru": "Модератор",
        "name_en": "Moderator",
        "emoji": "🔧",
        "color": "#ff9800",
        "perms": {
            "bypass_locks", "bypass_flood", "bypass_captcha",
            "warn", "mute", "kick", "delete", "purge",
            "report_view", "notes_manage", "filters_view",
            "approve", "lock_view",
        },
    },
    4: {
        "key": "senior",
        "name_ru": "Ст. модератор",
        "name_en": "Senior Mod",
        "emoji": "⚔",
        "color": "#e91e63",
        "perms": {
            "bypass_locks", "bypass_flood", "bypass_captcha",
            "warn", "mute", "kick", "ban", "tban", "delete", "purge",
            "report_view", "notes_manage", "filters_manage",
            "approve", "lock_manage", "welcome_view",
            "quarantine", "watch",
        },
    },
    5: {
        "key": "admin",
        "name_ru": "Администратор",
        "name_en": "Admin",
        "emoji": "⚙️",
        "color": "#9c27b0",
        "perms": {
            "bypass_locks", "bypass_flood", "bypass_captcha",
            "warn", "mute", "kick", "ban", "tban", "delete", "purge",
            "report_view", "notes_manage", "filters_manage",
            "approve", "lock_manage", "welcome_manage",
            "quarantine", "watch", "settings", "promote_helper",
            "promote_mod", "pin", "topics", "giveaway", "backup_view",
        },
    },
    6: {
        "key": "head",
        "name_ru": "Главный админ",
        "name_en": "Head Admin",
        "emoji": "💎",
        "color": "#00bcd4",
        "perms": {
            "bypass_locks", "bypass_flood", "bypass_captcha",
            "warn", "mute", "kick", "ban", "tban", "delete", "purge",
            "report_view", "notes_manage", "filters_manage",
            "approve", "lock_manage", "welcome_manage",
            "quarantine", "watch", "settings", "promote_helper",
            "promote_mod", "promote_admin", "pin", "topics",
            "giveaway", "backup_full", "federation", "nightmode",
            "raid", "forcesub", "mass_actions",
        },
    },
    7: {
        "key": "owner",
        "name_ru": "Владелец",
        "name_en": "Owner",
        "emoji": "👑",
        "color": "#ffd700",
        "perms": {"*"},  # everything
    },
}

RANK_BY_KEY = {v["key"]: k for k, v in RANKS.items()}

# Permission that Telegram admins automatically get mapped to
TG_ADMIN_MIN_RANK = 5  # "admin"
TG_CREATOR_RANK = 7    # "owner"


@dataclass
class RankInfo:
    level: int
    key: str
    name: str
    emoji: str
    perms: set[str]

    @property
    def display(self) -> str:
        return f"{self.emoji} {self.name}"

    def has(self, perm: str) -> bool:
        if "*" in self.perms:
            return True
        return perm in self.perms

    def can_manage(self, other_level: int) -> bool:
        """Can this rank promote/demote someone of other_level?"""
        return self.level > other_level


def get_rank_info(level: int, lang: str = "ru") -> RankInfo:
    level = max(0, min(7, int(level)))
    meta = RANKS[level]
    name = meta["name_ru"] if lang == "ru" else meta["name_en"]
    return RankInfo(
        level=level,
        key=meta["key"],
        name=name,
        emoji=meta["emoji"],
        perms=set(meta["perms"]),
    )


def rank_badge(level: int, lang: str = "ru") -> str:
    info = get_rank_info(level, lang)
    return f"{info.emoji} <b>{info.name}</b>"


def rank_list_text(lang: str = "ru") -> str:
    lines = []
    for lvl in range(7, -1, -1):
        info = get_rank_info(lvl, lang)
        lines.append(f"{info.emoji} <b>{info.name}</b> <code>[{lvl}]</code>")
    return "\n".join(lines)


# Which permissions are needed for common command groups
COMMAND_PERMS: dict[str, str] = {
    "warn": "warn",
    "dwarn": "warn",
    "unwarn": "warn",
    "mute": "mute",
    "tmute": "mute",
    "smute": "mute",
    "unmute": "mute",
    "kick": "kick",
    "dkick": "kick",
    "ban": "ban",
    "tban": "ban",
    "sban": "ban",
    "dban": "ban",
    "unban": "ban",
    "ro": "mute",
    "rw": "mute",
    "purge": "purge",
    "del": "delete",
    "delete": "delete",
    "lock": "lock_manage",
    "unlock": "lock_manage",
    "locks": "lock_view",
    "approve": "approve",
    "unapprove": "approve",
    "quarantine": "quarantine",
    "unquarantine": "quarantine",
    "watch": "watch",
    "unwatch": "watch",
    "settings": "settings",
    "setwelcome": "welcome_manage",
    "setrules": "welcome_manage",
    "filter": "filters_manage",
    "save": "notes_manage",
    "promote": "promote_mod",
    "demote": "promote_mod",
    "setrank": "promote_admin",
    "pin": "pin",
    "unpin": "pin",
    "gstart": "giveaway",
    "backup": "backup_view",
    "importbackup": "backup_full",
    "muteall": "mass_actions",
    "raid": "raid",
    "forcesub": "forcesub",
    "nightmode": "nightmode",
}


async def effective_rank(bot, chat_id: int, user_id: int) -> int:
    """Max of DB rank and Telegram admin status (creator=7, admin>=5)."""
    from config import config
    from core.permissions import admin_cache
    from database.extra import get_user_rank

    if config.is_owner(user_id):
        return 7
    db_level = await get_user_rank(chat_id, user_id)
    try:
        member = await admin_cache.get_member(bot, chat_id, user_id)
        status = getattr(member, "status", None) if member else None
        if status == "creator":
            return max(db_level, TG_CREATOR_RANK)
        if status in ("administrator", "creator"):
            return max(db_level, TG_ADMIN_MIN_RANK)
    except Exception:
        pass
    if await admin_cache.is_admin(bot, chat_id, user_id):
        return max(db_level, TG_ADMIN_MIN_RANK)
    return db_level


async def has_perm(bot, chat_id: int, user_id: int, perm: str) -> bool:
    level = await effective_rank(bot, chat_id, user_id)
    return get_rank_info(level).has(perm)


def perm_for_command(cmd: str) -> str | None:
    return COMMAND_PERMS.get((cmd or "").lower().lstrip("/"))
