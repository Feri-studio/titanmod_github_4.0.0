from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import mention, html_esc
from core.timeparse import parse_hhmm
from database.db import (
    update_settings, get_settings, approve_user, unapprove_user, is_approved,
    list_approved, add_report,
)
from handlers.common import resolve_user, MUTE_PERMS, FREE_PERMS
from core.permissions import admin_cache
from services.logger import send_log

router = Router()
router.message.filter(IsGroupFilter())


@router.message(Command("raid"), IsAdminFilter())
async def cmd_raid(message: Message, command: CommandObject):
    arg = (command.args or "on").strip().lower()
    on = arg in ("on", "1", "да", "yes")
    await update_settings(message.chat.id, raid_mode=1 if on else 0)
    await message.reply("Антирейд " + ("ВКЛЮЧЁН" if on else "выключен"))


@router.message(Command("forcesub"), IsAdminFilter())
async def cmd_forcesub(message: Message, command: CommandObject):
    arg = (command.args or "on").strip().lower()
    on = arg in ("on", "1", "да", "yes")
    await update_settings(message.chat.id, force_sub=1 if on else 0)
    await message.reply("Force-sub " + ("on. Задай канал: /setforcesub @channel" if on else "off"))


@router.message(Command("setforcesub"), IsAdminFilter())
async def cmd_setforcesub(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setforcesub @channel или id")
        return
    await update_settings(message.chat.id, force_sub_chat=command.args.strip(), force_sub=1)
    await message.reply(f"Канал обязательной подписки: {html_esc(command.args.strip())}")


@router.message(Command("antichannel"), IsAdminFilter())
async def cmd_antich(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, anti_channel=1 if on else 0)
    await message.reply("anti-channel " + ("on" if on else "off"))


@router.message(Command("nightmode"), IsAdminFilter())
async def cmd_night(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, nightmode=1 if on else 0)
    await message.reply("Ночной режим " + ("on" if on else "off"))


@router.message(Command("setnight"), IsAdminFilter())
async def cmd_setnight(message: Message, command: CommandObject):
    if not command.args or len(command.args.split()) < 2:
        await message.reply("/setnight 23:00 07:00")
        return
    a, b = command.args.split()[:2]
    if not parse_hhmm(a) or not parse_hhmm(b):
        await message.reply("Формат ЧЧ:ММ")
        return
    await update_settings(message.chat.id, night_start=a, night_end=b, nightmode=1)
    await message.reply(f"Ночь: {a} — {b}")


@router.message(Command("approve"), IsAdminFilter())
async def cmd_approve(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    await approve_user(message.chat.id, user.id, message.from_user.id)
    await message.reply(f"{mention(user)} исключён из фильтров.")


@router.message(Command("unapprove"), IsAdminFilter())
async def cmd_unapprove(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    await unapprove_user(message.chat.id, user.id)
    await message.reply("Снято.")


@router.message(Command("approved"), IsAdminFilter())
async def cmd_approved(message: Message):
    ids = await list_approved(message.chat.id)
    await message.reply("Approved:\n" + ("\n".join(f"<code>{i}</code>" for i in ids) or "пусто"))


@router.message(Command("report"))
async def cmd_report(message: Message, bot: Bot, command: CommandObject):
    s = await get_settings(message.chat.id)
    if not s.get("reports", 1):
        return
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение: /report причина")
        return
    target = message.reply_to_message.from_user
    reason = command.args or "Репорт"
    await add_report(message.chat.id, message.from_user.id, target.id, message.reply_to_message.message_id, reason)
    admins = await bot.get_chat_administrators(message.chat.id)
    mentions = " ".join(mention(a.user) for a in admins if not a.user.is_bot)[:800]
    text = f"Репорт от {mention(message.from_user)} на {mention(target)}\nПричина: {html_esc(reason)}\n{mentions}"
    await message.reply(text)
    await send_log(bot, message.chat.id, "report", text, target.id, message.from_user.id)


@router.message(Command("reports"), IsAdminFilter())
async def cmd_reports(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, reports=1 if on else 0)
    await message.reply("reports " + ("on" if on else "off"))


@router.message(Command("lockdown"), IsAdminFilter())
async def cmd_lockdown(message: Message, bot: Bot):
    try:
        await bot.set_chat_permissions(message.chat.id, MUTE_PERMS)
        await update_settings(message.chat.id, locked_until=1)
        await message.reply("Чат закрыт для участников.")
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("unlockdown"), IsAdminFilter())
async def cmd_unlockdown(message: Message, bot: Bot):
    try:
        await bot.set_chat_permissions(message.chat.id, FREE_PERMS)
        await update_settings(message.chat.id, locked_until=0)
        await message.reply("Чат открыт.")
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")
