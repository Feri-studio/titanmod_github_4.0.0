"""Group activation by secret code — only bot owner."""
from __future__ import annotations

from aiogram import Router, Bot, F
from aiogram.types import Message, ChatMemberUpdated
from aiogram.filters import Command, CommandObject, ChatMemberUpdatedFilter
from aiogram.filters.chat_member_updated import IS_NOT_MEMBER, IS_MEMBER, ADMINISTRATOR, MEMBER

from config import config
from core.style import ok, fail, HR, HR_LIGHT
from core.text import html_esc
from database.db import update_settings, get_settings, ensure_chat
from services.logger import send_log

router = Router()


@router.message(Command("activate", "активировать", "claim", "разблок"))
async def cmd_activate(message: Message, command: CommandObject, bot: Bot):
    if message.chat.type not in ("group", "supergroup"):
        await message.reply(
            "\n".join(
                [
                    "🔐 <b>Активация групп</b>",
                    HR,
                    "Эту команду нужно писать <b>в группе</b>, куда добавили бота.",
                    "",
                    f"Формат: <code>/activate {html_esc(config.ACTIVATE_CODE[:2])}…</code>",
                    HR_LIGHT,
                    "<i>Код знает только владелец бота</i>",
                ]
            )
        )
        return

    if not config.is_owner(message.from_user.id):
        await message.reply(
            fail(
                "Активировать группу может только <b>владелец бота</b> "
                "(id из <code>BOT_ADMINS</code>)."
            )
        )
        return

    code = (command.args or "").strip()
    if not code:
        await message.reply(
            "\n".join(
                [
                    "🔑 <b>Нужен код</b>",
                    HR,
                    "Напиши: <code>/activate ТВОЙ_КОД</code>",
                    "",
                    "Код выдаётся владельцем при настройке бота.",
                ]
            )
        )
        return

    if code != str(config.ACTIVATE_CODE):
        await message.reply(fail("Неверный код. Группа по-прежнему заблокирована."))
        return

    await ensure_chat(message.chat.id, message.chat.title, message.chat.type, message.chat.username)
    await update_settings(message.chat.id, group_activated=1)
    try:
        await send_log(
            bot, message.chat.id, "activate",
            f"✅ Группа активирована владельцем <code>{message.from_user.id}</code>",
            message.from_user.id, message.from_user.id,
        )
    except Exception:
        pass
    await message.reply(
        "\n".join(
            [
                "✅ <b>Группа активирована</b>",
                HR,
                f"Чат: <b>{html_esc(message.chat.title or str(message.chat.id))}</b>",
                "",
                "Теперь доступны модерация, ранги, экономика, настройки.",
                "› <code>/settings</code> · <code>/commands</code> · <code>/preset normal</code>",
                HR_LIGHT,
                "<i>TitanMod · спасибо, что подтвердили доступ</i>",
            ]
        )
    )
    try:
        for aid in config.ADMINS:
            if aid != message.from_user.id:
                await bot.send_message(
                    aid,
                    f"✅ Активирована группа <b>{html_esc(message.chat.title or '')}</b>\n"
                    f"<code>{message.chat.id}</code>",
                )
    except Exception:
        pass


@router.message(Command("deactivate", "деактивировать"), F.chat.type.in_({"group", "supergroup"}))
async def cmd_deactivate(message: Message):
    if not config.is_owner(message.from_user.id):
        await message.reply(fail("Только владелец бота."))
        return
    await update_settings(message.chat.id, group_activated=0)
    await message.reply(ok("Группа снова <b>заблокирована</b>. Нужен /activate КОД."))


@router.my_chat_member()
async def on_bot_added(event: ChatMemberUpdated, bot: Bot):
    """When bot is added to a group — show lock screen."""
    try:
        old = event.old_chat_member.status
        new = event.new_chat_member.status
        if new not in ("member", "administrator", "restricted"):
            return
        # only when bot was just added (was not in chat before)
        if old not in ("left", "kicked") and old is not None:
            if old in ("member", "administrator", "restricted", "creator"):
                return

        await ensure_chat(event.chat.id, event.chat.title, event.chat.type, event.chat.username)
        s = await get_settings(event.chat.id)
        if s.get("group_activated"):
            try:
                await bot.send_message(
                    event.chat.id,
                    f"✨ <b>TitanMod</b> на связи\n{HR}\nГруппа уже активирована. /commands",
                )
            except Exception:
                pass
            return

        # locked by default for new groups
        await update_settings(event.chat.id, group_activated=0)
        text = "\n".join(
            [
                "🔒 <b>TitanMod · нужен код</b>",
                HR,
                f"Меня добавили в <b>{html_esc(event.chat.title or 'чат')}</b>.",
                "",
                "Пока группа <b>не активирована</b> — я не выполняю команды.",
                "",
                "<b>Владелец бота</b>, напишите сюда:",
                "› <code>/activate ВАШ_КОД</code>",
                "",
                "Код есть только у владельца. Без него бот в этой группе бесполезен.",
                HR_LIGHT,
                "<i>Защита от добавления в чужие чаты</i>",
            ]
        )
        try:
            await bot.send_message(event.chat.id, text)
        except Exception:
            pass
        # notify owners
        for aid in config.ADMINS:
            try:
                await bot.send_message(
                    aid,
                    f"📥 Бота добавили в группу\n"
                    f"<b>{html_esc(event.chat.title or '')}</b>\n"
                    f"<code>{event.chat.id}</code>\n"
                    f"Статус: 🔒 ждёт /activate",
                )
            except Exception:
                pass
    except Exception:
        pass
