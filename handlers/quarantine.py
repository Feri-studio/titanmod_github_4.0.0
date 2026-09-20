import time
from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import mention, html_esc
from core.timeparse import parse_time, format_time
from database.extra import put_quarantine, get_quarantine, clear_quarantine
from database.db import get_settings, update_settings, ensure_chat
from handlers.common import MUTE_PERMS, FREE_PERMS, resolve_user
from services.logger import send_log

router = Router()


@router.message(Command("quarantine", "карантин"), IsAdminFilter(), IsGroupFilter())
async def cmd_q(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("/quarantine (ответ) 30m причина")
        return
    parts = (rest or "").split(maxsplit=1)
    seconds = parse_time(parts[0], 1800) if parts else 1800
    reason = parts[1] if len(parts) > 1 else "карантин"
    until = time.time() + seconds
    try:
        await bot.restrict_chat_member(message.chat.id, user.id, permissions=MUTE_PERMS)
    except Exception as e:
        await message.reply(html_esc(e))
        return
    await put_quarantine(message.chat.id, user.id, until, reason)
    await message.reply(
        f"🧪 {mention(user)} в карантине на {format_time(seconds)}\nПричина: {html_esc(reason)}"
    )
    await send_log(bot, message.chat.id, "quarantine", f"{mention(user)} {html_esc(reason)}", user.id, message.from_user.id)


@router.message(Command("unquarantine"), IsAdminFilter(), IsGroupFilter())
async def cmd_unq(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Ответь на пользователя.")
        return
    await clear_quarantine(message.chat.id, user.id)
    try:
        await bot.restrict_chat_member(message.chat.id, user.id, permissions=FREE_PERMS)
    except Exception:
        pass
    await message.reply(f"{mention(user)} снят с карантина.")


@router.message(Command("qstatus"), IsGroupFilter())
async def cmd_qstatus(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    user = user or message.from_user
    row = await get_quarantine(message.chat.id, user.id)
    if not row:
        await message.reply("Не в карантине.")
        return
    left = max(0, int(row["until_ts"] - time.time()))
    await message.reply(f"{mention(user)} карантин ещё {format_time(left)}\n{html_esc(row.get('reason') or '')}")


@router.message(Command("newusermute"), IsAdminFilter(), IsGroupFilter())
async def cmd_num(message: Message, command: CommandObject):
    if not command.args:
        s = await get_settings(message.chat.id)
        await message.reply(f"Мут новичков: {s.get('new_user_mute', 0)} сек (0=выкл)")
        return
    sec = parse_time(command.args.strip(), 0)
    await update_settings(message.chat.id, new_user_mute=sec)
    await message.reply(f"Новички будут в муте {format_time(sec) if sec else '0 (выкл)'}")


@router.message(Command("minage"), IsAdminFilter(), IsGroupFilter())
async def cmd_minage(message: Message, command: CommandObject):
    """Minimum Telegram account age in days (heuristic via user id is not possible; store setting for captcha policy)."""
    if not command.args or not command.args.strip().isdigit():
        s = await get_settings(message.chat.id)
        await message.reply(f"minage дней (информативно): {s.get('min_account_days', 0)}")
        return
    await update_settings(message.chat.id, min_account_days=int(command.args.strip()))
    await message.reply("Сохранено. Новые аккаунты будут проходить капчу строже.")
