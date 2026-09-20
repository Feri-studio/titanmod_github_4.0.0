from aiogram import Router, Bot, F
from aiogram.types import Message, ChatPermissions
from aiogram.filters import Command, CommandObject
from aiogram.enums import ChatType
from filters.admin import IsAdminFilter, IsGroupFilter
from database.db import (
    add_warn, remove_warn, get_warns, get_warns_count, clear_warns,
    add_punishment, get_chat, ensure_chat
)
from datetime import datetime, timedelta
import re

router = Router()
router.message.filter(IsGroupFilter())


def parse_time(time_str: str) -> int:
    """Парсит время типа 1h, 30m, 2d в секунды"""
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        return 3600  # по умолчанию 1 час
    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"s": 1, "m": 60, "h": 3600, "d": 86400}
    return value * multipliers.get(unit, 3600)


def get_mention(user) -> str:
    name = user.full_name or "User"
    return f'<a href="tg://user?id={user.id}">{name}</a>'


# ==================== BAN ====================

@router.message(Command("ban", "бан"), IsAdminFilter())
async def cmd_ban(message: Message, bot: Bot, command: CommandObject):
    if not message.reply_to_message and not command.args:
        await message.reply("Использование:\n• Ответь на сообщение: <code>/ban [причина]</code>\n• Или: <code>/ban @username [время] [причина]</code>")
        return

    target = message.reply_to_message.from_user if message.reply_to_message else None
    reason = "Без причины"
    until = None

    if command.args:
        parts = command.args.split(maxsplit=2)
        # Простая логика
        reason = command.args

    if not target:
        await message.reply("Ответь на сообщение пользователя, которого нужно забанить.")
        return

    if target.id == message.from_user.id:
        await message.reply("Нельзя забанить самого себя.")
        return

    try:
        await bot.ban_chat_member(message.chat.id, target.id)
        await add_punishment(message.chat.id, target.id, message.from_user.id, "ban", reason)
        
        text = (
            f"🚫 <b>Пользователь забанен</b>\n\n"
            f"👤 {get_mention(target)}\n"
            f"🛡 Админ: {get_mention(message.from_user)}\n"
            f"📝 Причина: {reason}"
        )
        await message.reply(text)
        
        # Лог
        await send_log(bot, message.chat.id, text)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@router.message(Command("unban", "разбан"), IsAdminFilter())
async def cmd_unban(message: Message, bot: Bot, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    try:
        await bot.unban_chat_member(message.chat.id, target.id, only_if_banned=True)
        await message.reply(f"✅ {get_mention(target)} разбанен.")
        await send_log(bot, message.chat.id, f"✅ Разбан: {get_mention(target)} от {get_mention(message.from_user)}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== MUTE ====================

@router.message(Command("mute", "мут"), IsAdminFilter())
async def cmd_mute(message: Message, bot: Bot, command: CommandObject):
    if not message.reply_to_message:
        await message.reply(
            "Использование:\n"
            "• <code>/mute</code> (на 1 час)\n"
            "• <code>/mute 2h</code>\n"
            "• <code>/mute 30m причина</code>\n"
            "Ответь на сообщение пользователя."
        )
        return

    target = message.reply_to_message.from_user
    time_sec = 3600
    reason = "Без причины"

    if command.args:
        parts = command.args.split(maxsplit=1)
        time_sec = parse_time(parts[0])
        if len(parts) > 1:
            reason = parts[1]

    until_date = datetime.now() + timedelta(seconds=time_sec)

    permissions = ChatPermissions(
        can_send_messages=False,
        can_send_media_messages=False,
        can_send_other_messages=False,
        can_add_web_page_previews=False
    )

    try:
        await bot.restrict_chat_member(
            message.chat.id,
            target.id,
            permissions=permissions,
            until_date=until_date
        )
        await add_punishment(message.chat.id, target.id, message.from_user.id, "mute", reason, until_date.isoformat())

        time_str = f"{time_sec // 60} мин." if time_sec < 3600 else f"{time_sec // 3600} ч."
        text = (
            f"🔇 <b>Пользователь замучен</b>\n\n"
            f"👤 {get_mention(target)}\n"
            f"⏱ Время: {time_str}\n"
            f"🛡 Админ: {get_mention(message.from_user)}\n"
            f"📝 Причина: {reason}"
        )
        await message.reply(text)
        await send_log(bot, message.chat.id, text)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@router.message(Command("unmute", "размут"), IsAdminFilter())
async def cmd_unmute(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_send_polls=True
    )
    try:
        await bot.restrict_chat_member(message.chat.id, target.id, permissions=permissions)
        await message.reply(f"🔊 {get_mention(target)} размучен.")
        await send_log(bot, message.chat.id, f"🔊 Размут: {get_mention(target)}")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== KICK ====================

@router.message(Command("kick", "кик"), IsAdminFilter())
async def cmd_kick(message: Message, bot: Bot, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    reason = command.args or "Без причины"

    try:
        await bot.ban_chat_member(message.chat.id, target.id)
        await bot.unban_chat_member(message.chat.id, target.id)  # сразу разбан = кик
        await add_punishment(message.chat.id, target.id, message.from_user.id, "kick", reason)

        text = (
            f"👢 <b>Пользователь кикнут</b>\n\n"
            f"👤 {get_mention(target)}\n"
            f"🛡 Админ: {get_mention(message.from_user)}\n"
            f"📝 Причина: {reason}"
        )
        await message.reply(text)
        await send_log(bot, message.chat.id, text)
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== WARN ====================

@router.message(Command("warn", "варн", "пред"), IsAdminFilter())
async def cmd_warn(message: Message, bot: Bot, command: CommandObject):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.\n<code>/warn [причина]</code>")
        return

    target = message.reply_to_message.from_user
    reason = command.args or "Без причины"

    chat = await ensure_chat(message.chat.id, message.chat.title)
    warn_limit = chat.get("warn_limit", 3)

    count = await add_warn(message.chat.id, target.id, message.from_user.id, reason)
    await add_punishment(message.chat.id, target.id, message.from_user.id, "warn", reason)

    text = (
        f"⚠️ <b>Предупреждение</b> [{count}/{warn_limit}]\n\n"
        f"👤 {get_mention(target)}\n"
        f"🛡 Админ: {get_mention(message.from_user)}\n"
        f"📝 Причина: {reason}"
    )
    await message.reply(text)
    await send_log(bot, message.chat.id, text)

    # Автобан при достижении лимита
    if count >= warn_limit:
        try:
            await bot.ban_chat_member(message.chat.id, target.id)
            await clear_warns(message.chat.id, target.id)
            ban_text = f"🚫 {get_mention(target)} забанен автоматически за {count} предупреждений."
            await message.answer(ban_text)
            await send_log(bot, message.chat.id, ban_text)
        except Exception as e:
            await message.answer(f"Не удалось забанить: {e}")


@router.message(Command("unwarn", "снятьварн"), IsAdminFilter())
async def cmd_unwarn(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    count = await remove_warn(message.chat.id, target.id)
    await message.reply(f"✅ Снято 1 предупреждение у {get_mention(target)}.\nОсталось: {count}")


@router.message(Command("warns", "варны"), IsAdminFilter())
async def cmd_warns(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    warns = await get_warns(message.chat.id, target.id)
    
    if not warns:
        await message.reply(f"У {get_mention(target)} нет предупреждений.")
        return

    text = f"⚠️ Предупреждения {get_mention(target)} ({len(warns)}):\n\n"
    for i, w in enumerate(warns, 1):
        text += f"{i}. {w['reason']} <i>({w['created_at'][:16]})</i>\n"
    await message.reply(text)


@router.message(Command("clearwarns", "очиститьварны"), IsAdminFilter())
async def cmd_clearwarns(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    await clear_warns(message.chat.id, target.id)
    await message.reply(f"✅ Все предупреждения {get_mention(target)} очищены.")


# ==================== INFO ====================

@router.message(Command("info", "инфо", "whois"), IsAdminFilter())
async def cmd_info(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение пользователя.")
        return

    target = message.reply_to_message.from_user
    warns_count = await get_warns_count(message.chat.id, target.id)

    try:
        member = await bot.get_chat_member(message.chat.id, target.id)
        status = member.status
    except:
        status = "unknown"

    text = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 ID: <code>{target.id}</code>\n"
        f"Имя: {get_mention(target)}\n"
        f"Username: @{target.username or 'нет'}\n"
        f"Статус: {status}\n"
        f"Предупреждения: {warns_count}"
    )
    await message.reply(text)


# ==================== RO / RW ====================

@router.message(Command("ro", "readonly"), IsAdminFilter())
async def cmd_ro(message: Message, bot: Bot, command: CommandObject):
    """Mute навсегда (read only)"""
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение.")
        return
    target = message.reply_to_message.from_user
    permissions = ChatPermissions(can_send_messages=False)
    try:
        await bot.restrict_chat_member(message.chat.id, target.id, permissions=permissions)
        await message.reply(f"🔇 {get_mention(target)} переведён в режим только чтения.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@router.message(Command("rw", "readwrite"), IsAdminFilter())
async def cmd_rw(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение.")
        return
    target = message.reply_to_message.from_user
    permissions = ChatPermissions(
        can_send_messages=True,
        can_send_media_messages=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True
    )
    try:
        await bot.restrict_chat_member(message.chat.id, target.id, permissions=permissions)
        await message.reply(f"🔊 {get_mention(target)} снова может писать.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== PURGE ====================

@router.message(Command("purge", "очистить"), IsAdminFilter())
async def cmd_purge(message: Message, bot: Bot, command: CommandObject):
    """Удаляет сообщения от reply до текущего"""
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение, с которого начать удаление.")
        return

    try:
        start_id = message.reply_to_message.message_id
        end_id = message.message_id
        deleted = 0
        for msg_id in range(start_id, end_id + 1):
            try:
                await bot.delete_message(message.chat.id, msg_id)
                deleted += 1
            except:
                pass
        status = await message.answer(f"🗑 Удалено сообщений: {deleted}")
        await status.delete()
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== PIN ====================

@router.message(Command("pin", "закрепить"), IsAdminFilter())
async def cmd_pin(message: Message, bot: Bot):
    if not message.reply_to_message:
        await message.reply("Ответь на сообщение, которое нужно закрепить.")
        return
    try:
        await bot.pin_chat_message(message.chat.id, message.reply_to_message.message_id)
        await message.reply("📌 Сообщение закреплено.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


@router.message(Command("unpin", "открепить"), IsAdminFilter())
async def cmd_unpin(message: Message, bot: Bot):
    try:
        await bot.unpin_chat_message(message.chat.id)
        await message.reply("📌 Сообщение откреплено.")
    except Exception as e:
        await message.reply(f"Ошибка: {e}")


# ==================== HELPERS ====================

async def send_log(bot: Bot, chat_id: int, text: str):
    """Отправляет лог в указанный чат, если настроен"""
    chat = await get_chat(chat_id)
    if chat and chat.get("log_chat_id"):
        try:
            await bot.send_message(chat["log_chat_id"], text, parse_mode="HTML")
        except:
            pass
