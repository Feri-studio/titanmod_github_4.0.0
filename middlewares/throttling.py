from aiogram import BaseMiddleware, Bot
from aiogram.types import Message
from aiogram.enums import ChatType
from typing import Callable, Dict, Any, Awaitable

from core.permissions import admin_cache
from core.timeparse import format_time
from database.db import check_flood, get_settings, is_approved, bump_stat, add_punishment
from aiogram.types import ChatPermissions
from datetime import datetime, timedelta


class AntiFloodMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message):
            return await handler(event, data)
        if event.chat.type not in (ChatType.GROUP, ChatType.SUPERGROUP):
            return await handler(event, data)
        if not event.from_user or event.from_user.is_bot:
            return await handler(event, data)

        bot: Bot = data["bot"]
        if await admin_cache.is_admin(bot, event.chat.id, event.from_user.id):
            return await handler(event, data)
        if await is_approved(event.chat.id, event.from_user.id):
            return await handler(event, data)

        settings = data.get("settings") or await get_settings(event.chat.id)
        if not settings.get("antiflood", 1):
            return await handler(event, data)

        text = event.text or event.caption or ""
        flooded, count = await check_flood(
            event.chat.id,
            event.from_user.id,
            int(settings.get("flood_limit", 6)),
            int(settings.get("flood_period", 8)),
            text,
        )
        if not flooded:
            return await handler(event, data)

        mode = settings.get("flood_mode", "mute")
        tsec = int(settings.get("flood_time", 300) or 300)
        try:
            await event.delete()
            await bump_stat(event.chat.id, "deleted")
        except Exception:
            pass
        uid = event.from_user.id
        try:
            if mode == "warn":
                from database.db import add_warn
                await add_warn(event.chat.id, uid, bot.id, "Антифлуд")
            elif mode == "kick":
                await bot.ban_chat_member(event.chat.id, uid)
                await bot.unban_chat_member(event.chat.id, uid)
                await bump_stat(event.chat.id, "kicks")
            elif mode == "ban":
                await bot.ban_chat_member(event.chat.id, uid)
                await bump_stat(event.chat.id, "bans")
            elif mode != "delete":
                until = datetime.utcnow() + timedelta(seconds=tsec)
                await bot.restrict_chat_member(
                    event.chat.id,
                    uid,
                    permissions=ChatPermissions(can_send_messages=False),
                    until_date=until,
                )
                await bump_stat(event.chat.id, "mutes")
            await add_punishment(event.chat.id, uid, bot.id, "flood", f"mode={mode} count={count}", None)
        except Exception:
            pass
        return None
