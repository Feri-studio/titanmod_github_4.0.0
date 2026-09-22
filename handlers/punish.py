from datetime import datetime, timedelta
from aiogram import Router, Bot, F
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsGroupFilter
from filters.rank import RankOrAdminFilter
from core.style import action_card, fail, need_reply, bad_args
from core.text import mention, html_esc
from core.timeparse import format_time
from database.db import add_punishment, bump_stat
from database.extra import bump_mod_stat
from handlers.common import (
    resolve_user, ensure_can_act, do_ban, do_mute, do_unmute, log_action, parse_time_reason, FREE_PERMS,
)

router = Router()
router.message.filter(IsGroupFilter())


def _usage_ban():
    return (
        "🔨 <b>Бан</b>\n"
        "──────────────\n"
        "Ответь на сообщение или укажи id.\n"
        "<code>/ban [время] [причина]</code>\n"
        "<code>/tban 2h спам</code>  ·  <code>/sban</code>  ·  <code>/dban</code>"
    )


@router.message(Command("ban", "бан"), RankOrAdminFilter("ban"))
async def cmd_ban(message: Message, bot: Bot, command: CommandObject):
    await _ban(message, bot, command.args or "", silent=False, delete=False, force_time=False)


@router.message(Command("sban", "сбан"), RankOrAdminFilter("ban"))
async def cmd_sban(message: Message, bot: Bot, command: CommandObject):
    await _ban(message, bot, command.args or "", silent=True, delete=False, force_time=False)


@router.message(Command("dban", "дбан"), RankOrAdminFilter("ban"))
async def cmd_dban(message: Message, bot: Bot, command: CommandObject):
    await _ban(message, bot, command.args or "", silent=False, delete=True, force_time=False)
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
        except Exception:
            pass


@router.message(Command("tban", "тбан"), RankOrAdminFilter("ban"))
async def cmd_tban(message: Message, bot: Bot, command: CommandObject):
    await _ban(message, bot, command.args or "", silent=False, delete=False, force_time=True)


async def _ban(message, bot, args, silent, delete, force_time):
    user, rest = await resolve_user(message, bot, args)
    err = await ensure_can_act(bot, message, user)
    if err:
        if not silent:
            await message.reply(err if user else need_reply("ban"))
        return
    seconds, reason, tstr = parse_time_reason(rest, 0)
    until = None
    extra = "Навсегда"
    if force_time or tstr:
        seconds = seconds or 3600
        until = datetime.utcnow() + timedelta(seconds=seconds)
        extra = f"Срок: {format_time(seconds)}"
    try:
        try:
            await bump_mod_stat(message.chat.id, message.from_user.id, "ban")
        except Exception:
            pass
        await do_ban(bot, message.chat.id, user.id, until)
        await add_punishment(message.chat.id, user.id, message.from_user.id, "ban", reason, extra)
        await bump_stat(message.chat.id, "bans")
        await log_action(bot, message, "BAN", user, reason, extra)
        if not silent:
            await message.reply(action_card("🚫 Бан", user, message.from_user, reason, extra))
        if delete:
            try:
                await message.delete()
            except Exception:
                pass
    except Exception as e:
        if not silent:
            err = str(e)
            if "not enough rights" in err.lower() or "can't restrict" in err.lower() or "CHAT_ADMIN_REQUIRED" in err:
                await message.reply("❌ Боту не хватает прав админа в этом чате (Ban users / Restrict).")
                return
            await message.reply(f"Ошибка: {err}")


@router.message(Command("unban", "разбан"), RankOrAdminFilter("ban"))
async def cmd_unban(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    try:
        await bot.unban_chat_member(message.chat.id, user.id, only_if_banned=True)
        await add_punishment(message.chat.id, user.id, message.from_user.id, "unban", rest or "")
        await log_action(bot, message, "UNBAN", user, rest or "—")
        await message.reply(action_card("✅ Разбан", user, message.from_user, rest or "—"))
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("kick", "кик"), RankOrAdminFilter("kick"))
async def cmd_kick(message: Message, bot: Bot, command: CommandObject):
    await _kick(message, bot, command.args or "", delete=False)


@router.message(Command("dkick"), RankOrAdminFilter("kick"))
async def cmd_dkick(message: Message, bot: Bot, command: CommandObject):
    await _kick(message, bot, command.args or "", delete=True)
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
        except Exception:
            pass


async def _kick(message, bot, args, delete):
    user, rest = await resolve_user(message, bot, args)
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    reason = rest or "Без причины"
    try:
        await bot.ban_chat_member(message.chat.id, user.id)
        await bot.unban_chat_member(message.chat.id, user.id)
        await add_punishment(message.chat.id, user.id, message.from_user.id, "kick", reason)
        await bump_stat(message.chat.id, "kicks")
        await log_action(bot, message, "KICK", user, reason)
        await message.reply(action_card("👢 Кик", user, message.from_user, reason))
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("kickme"))
async def cmd_kickme(message: Message, bot: Bot):
    try:
        await bot.ban_chat_member(message.chat.id, message.from_user.id)
        await bot.unban_chat_member(message.chat.id, message.from_user.id)
        await message.reply(f"{mention(message.from_user)} покинул чат по собственной воле.")
    except Exception as e:
        await message.reply(f"Не могу кикнуть: {html_esc(e)}")


@router.message(Command("banme"))
async def cmd_banme(message: Message, bot: Bot):
    await cmd_kickme(message, bot)


@router.message(Command("mute", "мут", "tmute", "тмут"), RankOrAdminFilter("mute"))
async def cmd_mute(message: Message, bot: Bot, command: CommandObject):
    await _mute(message, bot, command.args or "", silent=False)


@router.message(Command("smute"), RankOrAdminFilter("mute"))
async def cmd_smute(message: Message, bot: Bot, command: CommandObject):
    await _mute(message, bot, command.args or "", silent=True)


async def _mute(message, bot, args, silent):
    user, rest = await resolve_user(message, bot, args)
    err = await ensure_can_act(bot, message, user)
    if err:
        if not silent:
            await message.reply(err)
        return
    seconds, reason, tstr = parse_time_reason(rest, 3600)
    until = datetime.utcnow() + timedelta(seconds=seconds)
    try:
        await do_mute(bot, message.chat.id, user.id, until)
        extra = f"Срок: {format_time(seconds)}"
        await add_punishment(message.chat.id, user.id, message.from_user.id, "mute", reason, extra)
        await bump_stat(message.chat.id, "mutes")
        await log_action(bot, message, "MUTE", user, reason, extra)
        if not silent:
            await message.reply(action_card("🔇 Мут", user, message.from_user, reason, extra))
    except Exception as e:
        if not silent:
            err = str(e)
            if "not enough rights" in err.lower() or "can't restrict" in err.lower() or "CHAT_ADMIN_REQUIRED" in err:
                await message.reply("❌ Боту не хватает прав админа в этом чате (Ban users / Restrict).")
                return
            await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("unmute", "размут", "rw"), RankOrAdminFilter("mute"))
async def cmd_unmute(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    try:
        await do_unmute(bot, message.chat.id, user.id)
        await log_action(bot, message, "UNMUTE", user, rest or "—")
        await message.reply(action_card("🔊 Размут", user, message.from_user, rest or "—"))
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("ro", "readonly"), RankOrAdminFilter("mute"))
async def cmd_ro(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    err = await ensure_can_act(bot, message, user)
    if err:
        await message.reply(err)
        return
    try:
        await do_mute(bot, message.chat.id, user.id, None)
        await log_action(bot, message, "RO", user, rest or "read-only")
        await message.reply(action_card("👁‍🗨 Read-only", user, message.from_user, rest or "read-only"))
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("restrict"), RankOrAdminFilter("mute"))
async def cmd_restrict(message: Message, bot: Bot, command: CommandObject):
    await cmd_ro(message, bot, command)
