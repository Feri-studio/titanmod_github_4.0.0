try:
    from cachetools import TTLCache
except ImportError:
    class TTLCache(dict):
        def __init__(self, maxsize=0, ttl=0):
            super().__init__()

from aiogram import Bot
from aiogram.types import ChatMember, User

_cache = TTLCache(maxsize=5000, ttl=60)


class AdminCache:
    def __init__(self, ttl: int = 60):
        self.ttl = ttl

    @staticmethod
    def _key(chat_id: int, user_id: int) -> str:
        return f"{chat_id}:{user_id}"

    async def get_member(self, bot: Bot, chat_id: int, user_id: int) -> ChatMember | None:
        key = self._key(chat_id, user_id)
        if key in _cache:
            return _cache[key]
        try:
            member = await bot.get_chat_member(chat_id, user_id)
            _cache[key] = member
            return member
        except Exception:
            return None

    def invalidate(self, chat_id: int, user_id: int | None = None):
        if user_id is None:
            keys = [k for k in list(_cache.keys()) if str(k).startswith(f"{chat_id}:")]
            for k in keys:
                _cache.pop(k, None)
        else:
            _cache.pop(self._key(chat_id, user_id), None)

    async def is_admin(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        if not member:
            return False
        return member.status in ("creator", "administrator")

    async def is_creator(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        return bool(member and member.status == "creator")

    async def can_restrict(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        if not member:
            return False
        if member.status == "creator":
            return True
        if member.status == "administrator":
            return bool(getattr(member, "can_restrict_members", False))
        return False

    async def can_delete(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        if not member:
            return False
        if member.status == "creator":
            return True
        if member.status == "administrator":
            return bool(getattr(member, "can_delete_messages", False))
        return False

    async def can_promote(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        if not member:
            return False
        if member.status == "creator":
            return True
        return bool(getattr(member, "can_promote_members", False))

    async def can_pin(self, bot: Bot, chat_id: int, user_id: int) -> bool:
        member = await self.get_member(bot, chat_id, user_id)
        if not member:
            return False
        if member.status == "creator":
            return True
        return bool(getattr(member, "can_pin_messages", False))

    async def bot_can_restrict(self, bot: Bot, chat_id: int) -> bool:
        me = await bot.get_me()
        return await self.can_restrict(bot, chat_id, me.id)

    async def bot_can_delete(self, bot: Bot, chat_id: int) -> bool:
        me = await bot.get_me()
        return await self.can_delete(bot, chat_id, me.id)


admin_cache = AdminCache()


def is_user_admin_status(status: str) -> bool:
    return status in ("creator", "administrator")


def display_status(status: str) -> str:
    return {
        "creator": "владелец",
        "administrator": "админ",
        "member": "участник",
        "restricted": "ограничен",
        "left": "вышел",
        "kicked": "забанен",
    }.get(status, status or "неизвестно")


def user_from_member(member: ChatMember) -> User | None:
    return getattr(member, "user", None)
