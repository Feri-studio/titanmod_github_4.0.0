from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import mention, html_esc
from database.extra import watch_user, unwatch_user, is_watched, list_watches
from database.db import ensure_chat, add_event
from handlers.common import resolve_user
from services.logger import send_log

router = Router()


@router.message(Command("watch"), IsAdminFilter(), IsGroupFilter())
async def cmd_watch(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("/watch (ответ) [заметка]")
        return
    await watch_user(message.chat.id, user.id, message.from_user.id, rest or "")
    await message.reply(f"👁 Слежка за {mention(user)}")


@router.message(Command("unwatch"), IsAdminFilter(), IsGroupFilter())
async def cmd_unwatch(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Ответь на пользователя.")
        return
    await unwatch_user(message.chat.id, user.id)
    await message.reply(f"Слежка с {mention(user)} снята.")


@router.message(Command("watching"), IsAdminFilter(), IsGroupFilter())
async def cmd_watching(message: Message):
    rows = await list_watches(message.chat.id)
    if not rows:
        await message.reply("Никто не на присмотре.")
        return
    lines = ["👁 <b>Watchlist</b>"]
    for r in rows:
        lines.append(f"• <code>{r['user_id']}</code> — {html_esc(r.get('note') or '—')}")
    await message.reply("\n".join(lines))


@router.message(F.chat.type.in_({"group", "supergroup"}))
async def watch_listener(message: Message, bot: Bot):
    if not message.from_user:
        return
    if message.text and message.text.startswith("/"):
        return
    if not await is_watched(message.chat.id, message.from_user.id):
        return
    preview = html_esc((message.text or message.caption or message.content_type)[:300])
    await add_event(message.chat.id, "watch", message.from_user.id, None, preview)
    await send_log(
        bot,
        message.chat.id,
        "watch",
        f"👁 {mention(message.from_user)}: {preview}",
        message.from_user.id,
        None,
    )
