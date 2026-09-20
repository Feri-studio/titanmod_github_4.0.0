"""Extra admin and utility commands."""
from datetime import datetime, timedelta
from aiogram import Router, Bot, F
from aiogram.types import Message, ForumTopic
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter, IsPrivateFilter
from core.text import html_esc, mention
from database.db import update_settings, get_settings, connect_chat, get_connection, ensure_chat
from handlers.common import FREE_PERMS, MUTE_PERMS

router = Router()


@router.message(Command("slowmode"), IsAdminFilter(), IsGroupFilter())
async def cmd_slow(message: Message, bot: Bot, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/slowmode 10 — секунды (0 выкл)")
        return
    sec = max(0, min(int(command.args.strip()), 600))
    try:
        await bot.set_chat_slow_mode_delay(message.chat.id, sec)
        await update_settings(message.chat.id, slowmode=sec)
        await message.reply(f"Медленный режим: {sec} сек.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("setsticker"), IsAdminFilter(), IsGroupFilter())
async def cmd_setsticker(message: Message, bot: Bot):
    src = message.reply_to_message
    if not src or not src.sticker or not src.sticker.set_name:
        await message.reply("Ответь на стикер из набора.")
        return
    try:
        await bot.set_chat_sticker_set(message.chat.id, src.sticker.set_name)
        await message.reply("Набор стикеров чата обновлён.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("delsticker"), IsAdminFilter(), IsGroupFilter())
async def cmd_delsticker(message: Message, bot: Bot):
    try:
        await bot.delete_chat_sticker_set(message.chat.id)
        await message.reply("Набор стикеров сброшен.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("anonymous"), IsAdminFilter(), IsGroupFilter())
async def cmd_anon(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, anon_admin=1 if on else 0)
    await message.reply("Анонимные админы " + ("разрешены в настройках бота" if on else "будут раскрываться при возможности"))


@router.message(Command("permapin"), IsAdminFilter(), IsGroupFilter())
async def cmd_permapin(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение.")
        return
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id, disable_notification=True)
        await message.reply("Закреплено без уведомления.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("sd"), IsAdminFilter(), IsGroupFilter())
async def cmd_sd(message: Message, bot: Bot, command: CommandObject):
    """Self-destruct: send then delete after N seconds."""
    if not command.args:
        await message.reply("/sd 10 текст")
        return
    parts = command.args.split(maxsplit=1)
    try:
        sec = int(parts[0])
        text = parts[1] if len(parts) > 1 else "…"
    except Exception:
        await message.reply("Формат: /sd 10 текст")
        return
    try:
        await message.delete()
    except Exception:
        pass
    sent = await message.answer(text)
    import asyncio
    await asyncio.sleep(max(1, min(sec, 120)))
    try:
        await sent.delete()
    except Exception:
        pass


@router.message(Command("chatid"))
async def cmd_chatid(message: Message):
    await message.reply(f"<code>{message.chat.id}</code>")


@router.message(Command("userid"))
async def cmd_userid(message: Message):
    u = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    await message.reply(f"<code>{u.id}</code>")


@router.message(Command("fileid"))
async def cmd_fileid(message: Message):
    src = message.reply_to_message
    if not src:
        await message.reply("Ответь на медиа.")
        return
    for attr in ("photo", "document", "video", "audio", "voice", "sticker", "animation", "video_note"):
        val = getattr(src, attr, None)
        if not val:
            continue
        if attr == "photo":
            await message.reply(f"<code>{val[-1].file_id}</code>")
            return
        await message.reply(f"<code>{val.file_id}</code>")
        return
    await message.reply("Нет файла.")


@router.message(Command("members"), IsGroupFilter())
async def cmd_members(message: Message, bot: Bot):
    try:
        n = await bot.get_chat_member_count(message.chat.id)
        await message.reply(f"Участников: {n}")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("link"), IsGroupFilter())
async def cmd_public_link(message: Message):
    if message.chat.username:
        await message.reply(f"https://t.me/{message.chat.username}")
    else:
        await message.reply("Публичного username нет. Админ: /invitelink")


@router.message(Command("newtopic"), IsAdminFilter(), IsGroupFilter())
async def cmd_newtopic(message: Message, bot: Bot, command: CommandObject):
    if not command.args:
        await message.reply("/newtopic Название")
        return
    try:
        topic = await bot.create_forum_topic(message.chat.id, command.args.strip()[:128])
        await message.reply(f"Топик создан: {html_esc(topic.name)} id={topic.message_thread_id}")
    except Exception as e:
        await message.reply(f"Не форум или нет прав: {html_esc(e)}")


@router.message(Command("closetopic"), IsAdminFilter(), IsGroupFilter())
async def cmd_closetopic(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        await message.reply("Пиши в топике.")
        return
    try:
        await bot.close_forum_topic(message.chat.id, tid)
        await message.reply("Топик закрыт.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("reopentopic"), IsAdminFilter(), IsGroupFilter())
async def cmd_reopen(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        return
    try:
        await bot.reopen_forum_topic(message.chat.id, tid)
        await message.reply("Топик открыт.")
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("deletetopic"), IsAdminFilter(), IsGroupFilter())
async def cmd_deltopic(message: Message, bot: Bot):
    tid = message.message_thread_id
    if not tid:
        return
    try:
        await bot.delete_forum_topic(message.chat.id, tid)
    except Exception as e:
        await message.reply(html_esc(e))


@router.message(Command("connectid"), IsPrivateFilter())
async def cmd_connectid(message: Message, bot: Bot, command: CommandObject):
    if not command.args or not command.args.strip().lstrip("-").isdigit():
        await message.reply("В группе: /connect\nВ ЛС: /connectid -100...")
        return
    cid = int(command.args.strip())
    try:
        mem = await bot.get_chat_member(cid, message.from_user.id)
        if mem.status not in ("creator", "administrator"):
            await message.reply("Ты не админ там.")
            return
    except Exception as e:
        await message.reply(f"Не вижу этот чат: {html_esc(e)}")
        return
    await connect_chat(message.from_user.id, cid)
    await message.reply(f"Привязан чат <code>{cid}</code>")


@router.message(Command("connection"))
async def cmd_connection(message: Message):
    cid = await get_connection(message.from_user.id)
    await message.reply(f"Привязка: <code>{cid or 'нет'}</code>")


@router.message(Command("setfloodtime"), IsAdminFilter(), IsGroupFilter())
async def cmd_floodtime(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/setfloodtime 300")
        return
    await update_settings(message.chat.id, flood_time=int(command.args.strip()))
    await message.reply("Время наказания антифлуда обновлено.")


@router.message(Command("setwarntime"), IsAdminFilter(), IsGroupFilter())
async def cmd_warntime(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/setwarntime 0  (0 = навсегда при бане)")
        return
    await update_settings(message.chat.id, warn_time=int(command.args.strip()))
    await message.reply("Время наказания за варны обновлено.")


@router.message(Command("allowlist"), IsAdminFilter(), IsGroupFilter())
async def cmd_allowlist(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, allow_list_only=1 if on else 0)
    await message.reply("Режим только approved " + ("ON — писать могут только approved и админы" if on else "OFF"))


@router.message(Command("maxfile"), IsAdminFilter(), IsGroupFilter())
async def cmd_maxfile(message: Message, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/maxfile 20  (МБ, 0 = без лимита)")
        return
    await update_settings(message.chat.id, max_file_mb=int(command.args.strip()))
    await message.reply("Лимит файла обновлён.")


@router.message(Command("blockext"), IsAdminFilter(), IsGroupFilter())
async def cmd_blockext(message: Message, command: CommandObject):
    if not command.args:
        s = await get_settings(message.chat.id)
        await message.reply("Сейчас: " + html_esc(s.get("blocked_ext") or ""))
        return
    await update_settings(message.chat.id, blocked_ext=command.args.replace(" ", ""))
    await message.reply("Расширения обновлены.")


@router.message(Command("setraid"), IsAdminFilter(), IsGroupFilter())
async def cmd_setraid(message: Message, command: CommandObject):
    if not command.args:
        await message.reply("/setraid 10 12 mute — joins, окно сек, действие")
        return
    a = command.args.split()
    try:
        joins, window = int(a[0]), int(a[1]) if len(a) > 1 else 12
        action = a[2] if len(a) > 2 else "mute"
        await update_settings(message.chat.id, raid_joins=joins, raid_window=window, raid_action=action)
        await message.reply("Антирейд обновлён.")
    except Exception:
        await message.reply("Формат: /setraid 10 12 mute")


@router.message(Command("welcomemute"), IsAdminFilter(), IsGroupFilter())
async def cmd_wmute(message: Message, command: CommandObject):
    on = (command.args or "on").lower() in ("on", "1", "да")
    await update_settings(message.chat.id, welcome_mute=1 if on else 0)
    await message.reply("welcome mute " + ("on" if on else "off"))


@router.message(Command("pingadmins"), IsGroupFilter())
async def cmd_pingadmins(message: Message, bot: Bot):
    s = await get_settings(message.chat.id)
    if not s.get("reports", 1) and not await _is_admin(bot, message):
        return
    admins = await bot.get_chat_administrators(message.chat.id)
    text = " ".join(mention(a.user) for a in admins if not a.user.is_bot)[:1000]
    await message.reply("Админы: " + (text or "нет"))


async def _is_admin(bot, message):
    from core.permissions import admin_cache
    return await admin_cache.is_admin(bot, message.chat.id, message.from_user.id)
