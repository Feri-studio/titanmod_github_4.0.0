"""Support tickets system — TitanMod 4.x."""
from __future__ import annotations

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.style import card, ok, fail, HR, HR_LIGHT, safe_edit, safe_answer
from core.text import html_esc, mention
from database.extra import (
    create_ticket, add_ticket_message, get_ticket, list_tickets,
    close_ticket, list_ticket_messages,
)

router = Router()


def tickets_kb(rows: list[dict]) -> object:
    b = InlineKeyboardBuilder()
    for t in rows[:12]:
        st = "🟢" if t.get("status") == "open" else "⚫"
        b.row(InlineKeyboardButton(
            text=f"{st} #{t['id']} {(t.get('subject') or '')[:24]}",
            callback_data=f"tkt:view:{t['id']}",
        ))
    b.row(InlineKeyboardButton(text="✖ Закрыть", callback_data="tkt:close_ui"))
    return b.as_markup()


@router.message(Command("ticket", "тикет", "support"))
async def cmd_ticket(message: Message, command: CommandObject):
    subject = (command.args or "").strip() or "Без темы"
    if len(subject) > 200:
        subject = subject[:200]
    body = ""
    if message.reply_to_message and message.reply_to_message.text:
        body = message.reply_to_message.text[:2000]
    tid = await create_ticket(
        user_id=message.from_user.id,
        subject=subject,
        chat_id=message.chat.id if message.chat.type != "private" else None,
        first_message=body or subject,
    )
    await message.reply(
        card(
            f"Тикет #{tid}",
            f"Тема: <b>{html_esc(subject)}</b>\n"
            f"Статус: <b>open</b>\n"
            f"Ответить: <code>/reply {tid} текст</code>\n"
            f"Закрыть: <code>/close {tid}</code>",
            footer="Владелец бота увидит обращение",
            emoji="🎫",
        )
    )
    # notify bot owners
    for admin_id in config.ADMINS:
        try:
            await message.bot.send_message(
                admin_id,
                f"🎫 Новый тикет <b>#{tid}</b> от {mention(message.from_user)}\n"
                f"Тема: {html_esc(subject)}\n"
                f"<code>/reply {tid} …</code>",
            )
        except Exception:
            pass


@router.message(Command("reply", "treply"))
async def cmd_reply_ticket(message: Message, command: CommandObject, bot: Bot):
    parts = (command.args or "").split(maxsplit=1)
    if len(parts) < 2 or not parts[0].isdigit():
        await message.reply("Формат: <code>/reply 12 текст ответа</code>")
        return
    tid = int(parts[0])
    text = parts[1].strip()
    t = await get_ticket(tid)
    if not t:
        await message.reply(fail("Тикет не найден"))
        return
    is_staff = config.is_owner(message.from_user.id)
    is_owner_tkt = t["user_id"] == message.from_user.id
    if not (is_staff or is_owner_tkt):
        await message.reply(fail("Нет доступа к этому тикету"))
        return
    if t.get("status") != "open":
        await message.reply(fail("Тикет уже закрыт"))
        return
    await add_ticket_message(tid, message.from_user.id, text)
    await message.reply(ok(f"Ответ в тикет #{tid} записан"))
    # notify other side
    target = t["user_id"] if is_staff else (config.ADMINS[0] if config.ADMINS else None)
    if target and target != message.from_user.id:
        try:
            await bot.send_message(
                target,
                f"🎫 Тикет <b>#{tid}</b>\n{mention(message.from_user)}:\n{html_esc(text)}",
            )
        except Exception:
            pass


@router.message(Command("close", "tclose"))
async def cmd_close_ticket(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw.isdigit():
        await message.reply("<code>/close 12</code>")
        return
    tid = int(raw)
    t = await get_ticket(tid)
    if not t:
        await message.reply(fail("Не найден"))
        return
    if not (config.is_owner(message.from_user.id) or t["user_id"] == message.from_user.id):
        await message.reply(fail("Нет прав"))
        return
    await close_ticket(tid, message.from_user.id)
    await message.reply(ok(f"Тикет #{tid} закрыт"))


@router.message(Command("tickets", "тикеты"))
async def cmd_tickets(message: Message):
    if not config.is_owner(message.from_user.id):
        # user sees own tickets
        rows = await list_tickets(user_id=message.from_user.id, limit=20)
    else:
        rows = await list_tickets(status="open", limit=20)
    if not rows:
        await message.reply("🎫 Открытых тикетов нет")
        return
    lines = [f"🎫 <b>Тикеты</b>", HR]
    for t in rows:
        lines.append(
            f"#{t['id']} · {html_esc(t.get('subject') or '—')} · "
            f"<code>{t.get('status')}</code> · uid <code>{t['user_id']}</code>"
        )
    await message.reply("\n".join(lines), reply_markup=tickets_kb(rows))


@router.callback_query(F.data.startswith("tkt:"))
async def tkt_cb(callback: CallbackQuery):
    parts = callback.data.split(":")
    if parts[1] == "close_ui":
        try:
            await callback.message.delete()
        except Exception:
            pass
        await safe_answer(callback)
        return
    if parts[1] == "view" and parts[2].isdigit():
        tid = int(parts[2])
        t = await get_ticket(tid)
        if not t:
            await safe_answer(callback, "Не найден", show_alert=True)
            return
        msgs = await list_ticket_messages(tid, limit=15)
        body = [
            f"Тема: <b>{html_esc(t.get('subject') or '')}</b>",
            f"Статус: <code>{t.get('status')}</code>",
            f"Автор: <code>{t['user_id']}</code>",
            HR_LIGHT,
        ]
        for m in msgs:
            body.append(f"<code>{m['user_id']}</code>: {html_esc((m.get('text') or '')[:200])}")
        await safe_edit(callback.message, card(f"Тикет #{tid}", "\n".join(body), emoji="🎫"))
    await safe_answer(callback)
