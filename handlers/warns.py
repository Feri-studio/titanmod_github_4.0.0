from datetime import datetime, timedelta
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.style import action_card, HR
from core.text import mention, html_esc
from core.timeparse import format_time, parse_time
from database.db import (
    add_warn, remove_warn, get_warns, get_warns_count, clear_warns,
    add_punishment, bump_stat, get_settings, update_settings, ensure_chat,
)
from handlers.common import resolve_user, ensure_can_act, do_ban, do_mute, log_action

router = Router()
router.message.filter(IsGroupFilter())


async def apply_warn_limit(bot, message, target, count, settings):
    limit = int(settings.get("warn_limit", 3) or 3)
    if count < limit:
        return False
    mode = settings.get("warn_mode", "ban")
    tsec = int(settings.get("warn_time", 0) or 0)
    await clear_warns(message.chat.id, target.id)
    try:
        if mode in ("mute", "tmute"):
            until = datetime.utcnow() + timedelta(seconds=tsec or 3600)
            await do_mute(bot, message.chat.id, target.id, until)
            await bump_stat(message.chat.id, "mutes")
            await message.answer(f"{mention(target)} замучен за {count} предупреждений.")
        elif mode == "kick":
            await bot.ban_chat_member(message.chat.id, target.id)
            await bot.unban_chat_member(message.chat.id, target.id)
            await bump_stat(message.chat.id, "kicks")
            await message.answer(f"{mention(target)} кикнут за {count} предупреждений.")
        else:
            until = datetime.utcnow() + timedelta(seconds=tsec) if tsec else None
            await do_ban(bot, message.chat.id, target.id, until)
            await bump_stat(message.chat.id, "bans")
            extra = format_time(tsec) if tsec else "навсегда"
            await message.answer(f"{mention(target)} забанен за {count} предупреждений ({extra}).")
    except Exception as e:
        await message.answer(f"Лимит варнов достигнут, но наказание не применилось: {html_esc(e)}")
    return True


@router.message(Command("warn", "варн", "пред", "dwarn"), IsAdminFilter())
async def cmd_warn(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    reason = rest or "Без причины"
    if command.command == "dwarn" and message.reply_to_message:
        try:
            await message.reply_to_message.delete()
        except Exception:
            pass
    settings = await get_settings(message.chat.id)
    limit = int(settings.get("warn_limit", 3) or 3)
    count = await add_warn(message.chat.id, user.id, message.from_user.id, reason)
    await add_punishment(message.chat.id, user.id, message.from_user.id, "warn", reason)
    await bump_stat(message.chat.id, "warns")
    await log_action(bot, message, "WARN", user, reason, f"{count}/{limit}")
    await message.reply(action_card(f"⚠️ Варн [{count}/{limit}]", user, message.from_user, reason))
    await apply_warn_limit(bot, message, user, count, settings)


@router.message(Command("unwarn", "снятьварн"), IsAdminFilter())
async def cmd_unwarn(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    count = await remove_warn(message.chat.id, user.id, 1)
    await message.reply(f"Снято 1 предупреждение у {mention(user)}. Осталось: {count}")


@router.message(Command("warns", "варны"), IsAdminFilter())
async def cmd_warns(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    warns = await get_warns(message.chat.id, user.id)
    if not warns:
        await message.reply(f"У {mention(user)} нет предупреждений.")
        return
    lines = [f"⚠️ <b>Варны</b> {mention(user)} · {len(warns)}", HR]
    for i, w in enumerate(warns[:20], 1):
        lines.append(f"{i}. {html_esc(w['reason'])} <i>({str(w['created_at'])[:16]})</i>")
    await message.reply("\n".join(lines))


@router.message(Command("clearwarns", "resetwarns", "очиститьварны"), IsAdminFilter())
async def cmd_clear(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    await clear_warns(message.chat.id, user.id)
    await message.reply(f"Все предупреждения {mention(user)} очищены.")


@router.message(Command("setwarnlimit"), IsAdminFilter())
async def cmd_setwarnlimit(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("Использование: <code>/setwarnlimit 3</code>")
        return
    n = int(command.args.strip())
    n = max(1, min(n, 50))
    await update_settings(message.chat.id, warn_limit=n)
    await message.reply(f"Лимит предупреждений: {n}")


@router.message(Command("warnmode"), IsAdminFilter())
async def cmd_warnmode(message: Message, command: CommandObject):
    arg = (command.args or "").strip().lower()
    if arg not in ("ban", "mute", "kick", "tban", "tmute"):
        await message.reply("Режимы: ban, mute, kick, tban, tmute")
        return
    await update_settings(message.chat.id, warn_mode=arg)
    await message.reply(f"Действие при лимите варнов: <code>{arg}</code>")
