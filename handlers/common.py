from datetime import datetime, timedelta
from aiogram import Bot
from aiogram.types import Message, ChatPermissions, User
from core.style import action_card
from core.timeparse import parse_time, format_time
from core.permissions import admin_cache
from database.db import add_punishment, bump_stat
from services.logger import send_log
from utils.target import extract_target, extract_reason


MUTE_PERMS = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)

FREE_PERMS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def resolve_user(message: Message, bot: Bot, args: str):
    user, rest = await extract_target(message, args)
    if user and user.first_name != str(user.id):
        return user, rest
    if user and user.first_name == str(user.id):
        try:
            member = await bot.get_chat_member(message.chat.id, user.id)
            return member.user, rest
        except Exception:
            return user, rest
    # Try @username via Telegram API
    token = (args or "").strip().split(maxsplit=1)
    if token and token[0].startswith("@"):
        uname = token[0].lstrip("@")
        leftover = token[1] if len(token) > 1 else ""
        try:
            chat = await bot.get_chat(f"@{uname}")
            if getattr(chat, "type", None) == "private" or getattr(chat, "id", None):
                u = User(
                    id=chat.id,
                    is_bot=bool(getattr(chat, "is_bot", False)),
                    first_name=getattr(chat, "first_name", None) or uname,
                    last_name=getattr(chat, "last_name", None),
                    username=getattr(chat, "username", None) or uname,
                )
                return u, leftover
        except Exception:
            pass
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, rest
    return None, rest


async def ensure_can_act(bot: Bot, message: Message, target: User) -> str | None:
    if not target:
        return "Укажи пользователя ответом, id или упоминанием."
    if target.id == (await bot.get_me()).id:
        return "Нельзя применить это ко мне."
    if target.id == message.from_user.id:
        return "Нельзя применить это к себе."
    if await admin_cache.is_admin(bot, message.chat.id, target.id):
        return "Нельзя наказать администратора."
    # Rank hierarchy: cannot punish equal/higher rank
    try:
        from core.ranks import effective_rank
        actor = await effective_rank(bot, message.chat.id, message.from_user.id)
        victim = await effective_rank(bot, message.chat.id, target.id)
        if victim >= actor and victim > 0:
            return "Нельзя наказать участника с равным или более высоким рангом."
    except Exception:
        pass
    return None


async def do_ban(bot, chat_id, target_id, until=None):
    kwargs = {}
    if until:
        kwargs["until_date"] = until
    await bot.ban_chat_member(chat_id, target_id, **kwargs)


async def do_mute(bot, chat_id, target_id, until=None):
    kwargs = {"permissions": MUTE_PERMS}
    if until:
        kwargs["until_date"] = until
    await bot.restrict_chat_member(chat_id, target_id, **kwargs)


async def do_unmute(bot, chat_id, target_id):
    await bot.restrict_chat_member(chat_id, target_id, permissions=FREE_PERMS)


async def log_action(bot, message, action, target, reason, extra=""):
    text = action_card(action, target, message.from_user, reason, extra)
    await send_log(bot, message.chat.id, action.lower(), text, target.id if target else None, message.from_user.id)


def parse_time_reason(args: str, default_time=3600):
    tstr, reason = extract_reason(args)
    seconds = parse_time(tstr, default_time) if tstr else default_time
    return seconds, reason, tstr
