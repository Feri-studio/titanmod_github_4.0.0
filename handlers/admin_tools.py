from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import mention, html_esc
from core.permissions import admin_cache
from database.db import (
    update_settings, get_settings, disable_command, enable_command, list_disabled,
    connect_chat, disconnect_chat, get_connection, export_chat, reset_settings,
)
from core.commands import DISABLEABLE
from handlers.common import resolve_user
import json

router = Router()


@router.message(Command("promote"), IsAdminFilter(), IsGroupFilter())
async def cmd_promote(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    try:
        await bot.promote_chat_member(
            message.chat.id, user.id,
            can_delete_messages=True,
            can_restrict_members=True,
            can_invite_users=True,
            can_pin_messages=True,
            can_manage_chat=True,
        )
        title = rest.strip()[:16] if rest else "Admin"
        try:
            await bot.set_chat_administrator_custom_title(message.chat.id, user.id, title)
        except Exception:
            pass
        admin_cache.invalidate(message.chat.id, user.id)
        await message.reply(f"{mention(user)} назначен админом.")
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("demote"), IsAdminFilter(), IsGroupFilter())
async def cmd_demote(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    try:
        await bot.promote_chat_member(
            message.chat.id, user.id,
            is_anonymous=False,
            can_manage_chat=False,
            can_delete_messages=False,
            can_manage_video_chats=False,
            can_restrict_members=False,
            can_promote_members=False,
            can_change_info=False,
            can_invite_users=False,
            can_pin_messages=False,
        )
        admin_cache.invalidate(message.chat.id, user.id)
        await message.reply(f"{mention(user)} снят с админки.")
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("adminlist", "staff"), IsGroupFilter())
async def cmd_admins(message: Message, bot: Bot):
    admins = await bot.get_chat_administrators(message.chat.id)
    lines = ["Админы:"]
    for a in admins:
        mark = "владелец" if a.status == "creator" else "админ"
        lines.append(f"• {mention(a.user)} — {mark}")
    await message.reply("\n".join(lines))


@router.message(Command("admincache"), IsAdminFilter(), IsGroupFilter())
async def cmd_admincache(message: Message):
    admin_cache.invalidate(message.chat.id)
    await message.reply("Кэш админов сброшен.")


@router.message(Command("invitelink"), IsAdminFilter(), IsGroupFilter())
async def cmd_link(message: Message, bot: Bot):
    try:
        link = await bot.export_chat_invite_link(message.chat.id)
        await message.reply(f"Ссылка: {html_esc(link)}")
    except Exception as e:
        await message.reply(f"Ошибка: {html_esc(e)}")


@router.message(Command("setgtitle"), IsAdminFilter(), IsGroupFilter())
async def cmd_title(message: Message, bot: Bot, command: CommandObject):
    if not command.args:
        return
    try:
        await bot.set_chat_title(message.chat.id, command.args)
        await message.reply("Название обновлено.")
    except Exception as e:
        await message.reply(str(e))


@router.message(Command("setgdesc"), IsAdminFilter(), IsGroupFilter())
async def cmd_desc(message: Message, bot: Bot, command: CommandObject):
    try:
        await bot.set_chat_description(message.chat.id, command.args or "")
        await message.reply("Описание обновлено.")
    except Exception as e:
        await message.reply(str(e))


@router.message(Command("pin"), IsAdminFilter(), IsGroupFilter())
async def cmd_pin(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение.")
        return
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("Закреплено.")
    except Exception as e:
        await message.reply(str(e))


@router.message(Command("unpin"), IsAdminFilter(), IsGroupFilter())
async def cmd_unpin(message: Message, bot: Bot):
    try:
        mid = message.reply_to_message.message_id if message.reply_to_message else None
        await bot.unpin_chat_message(message.chat.id, mid)
        await message.reply("Откреплено.")
    except Exception as e:
        await message.reply(str(e))


@router.message(Command("unpinall"), IsAdminFilter(), IsGroupFilter())
async def cmd_unpinall(message: Message, bot: Bot):
    try:
        await bot.unpin_all_chat_messages(message.chat.id)
        await message.reply("Все закрепы сняты.")
    except Exception as e:
        await message.reply(str(e))


@router.message(Command("purge", "spurge"), IsAdminFilter(), IsGroupFilter())
async def cmd_purge(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение, с которого удалять.")
        return
    silent = message.text.startswith("/spurge")
    start, end = message.reply_to_message.message_id, message.message_id
    deleted = 0
    for mid in range(start, end + 1):
        try:
            await bot.delete_message(message.chat.id, mid)
            deleted += 1
        except Exception:
            pass
    if not silent:
        msg = await message.answer(f"Удалено: {deleted}")
        try:
            await msg.delete()
        except Exception:
            pass


@router.message(Command("del"), IsAdminFilter(), IsGroupFilter())
async def cmd_del(message: Message, bot: Bot):
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
        except Exception:
            pass
    try:
        await message.delete()
    except Exception:
        pass


@router.message(Command("setlog"), IsAdminFilter(), IsGroupFilter())
async def cmd_setlog(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setlog chat_id")
        return
    try:
        await update_settings(message.chat.id, log_chat_id=int(command.args.strip()))
        await message.reply("Логи включены.")
    except Exception:
        await message.reply("Неверный id.")


@router.message(Command("unsetlog"), IsAdminFilter(), IsGroupFilter())
async def cmd_unsetlog(message: Message):
    await update_settings(message.chat.id, log_chat_id=None)
    await message.reply("Логи выключены.")


@router.message(Command("disable"), IsAdminFilter(), IsGroupFilter())
async def cmd_disable(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("Команды: " + ", ".join(f"/{c}" for c in DISABLEABLE[:40]))
        return
    cmd = command.args.strip().lstrip("/").lower()
    if cmd not in DISABLEABLE:
        await message.reply("Эту команду нельзя выключить.")
        return
    await disable_command(message.chat.id, cmd)
    await message.reply(f"/{cmd} выключена в этом чате.")


@router.message(Command("enable"), IsAdminFilter(), IsGroupFilter())
async def cmd_enable(message: Message, command: CommandObject):
    if not command.args:
        return
    await enable_command(message.chat.id, command.args.strip().lstrip("/"))
    await message.reply("Включено.")


@router.message(Command("disabled"), IsAdminFilter(), IsGroupFilter())
async def cmd_disabled(message: Message):
    items = await list_disabled(message.chat.id)
    await message.reply("Выключено:\n" + (", ".join(f"/{i}" for i in items) or "ничего"))


@router.message(Command("connect"), IsGroupFilter(), IsAdminFilter())
async def cmd_connect(message: Message):
    await connect_chat(message.from_user.id, message.chat.id)
    await message.reply("Чат привязан. Команды из ЛС будут применяться сюда.")


@router.message(Command("disconnect"))
async def cmd_disconnect(message: Message):
    await disconnect_chat(message.from_user.id)
    await message.reply("Отвязано.")


@router.message(Command("export"), IsAdminFilter(), IsGroupFilter())
async def cmd_export(message: Message):
    data = await export_chat(message.chat.id)
    raw = json.dumps(data, ensure_ascii=False, indent=2)
    if len(raw) > 3500:
        raw = raw[:3500] + "\n…"
    await message.reply(f"<pre>{html_esc(raw)}</pre>")


@router.message(Command("resetchat"), IsAdminFilter(), IsGroupFilter())
async def cmd_reset(message: Message):
    await reset_settings(message.chat.id)
    await message.reply("Настройки чата сброшены.")


@router.message(Command("setlang"), IsAdminFilter(), IsGroupFilter())
async def cmd_lang(message: Message, command: CommandObject):
    lang = (command.args or "ru").strip().lower()
    if lang not in ("ru", "en"):
        await message.reply("ru или en")
        return
    await update_settings(message.chat.id, lang=lang)
    await message.reply(f"Язык: {lang}")
