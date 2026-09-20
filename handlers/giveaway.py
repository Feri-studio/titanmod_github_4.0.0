import random
import time
from aiogram import Router, Bot, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandObject
from filters.admin import IsAdminFilter, IsGroupFilter
from core.text import html_esc, mention
from core.timeparse import parse_time, format_time
from database.extra import (
    create_giveaway, set_giveaway_message, get_giveaway, join_giveaway,
    giveaway_members, close_giveaway,
)

router = Router()


def g_kb(gid: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎁 Участвовать", callback_data=f"gjoin:{gid}")]
    ])


@router.message(Command("gstart", "giveaway", "розыгрыш"), IsAdminFilter(), IsGroupFilter())
async def cmd_gstart(message: Message, bot: Bot, command: CommandObject):
    if not command.args:
        await message.reply("/gstart 1h 1 iPhone\nФормат: время [число победителей] приз")
        return
    parts = command.args.split(maxsplit=2)
    seconds = parse_time(parts[0], 3600)
    winners = 1
    prize = command.args
    if len(parts) >= 2 and parts[1].isdigit():
        winners = max(1, min(int(parts[1]), 20))
        prize = parts[2] if len(parts) > 2 else "Приз"
    elif len(parts) >= 2:
        prize = " ".join(parts[1:])
    closes = time.time() + seconds
    gid = await create_giveaway(message.chat.id, message.from_user.id, prize, winners, closes)
    text = (
        f"🎉 <b>Розыгрыш #{gid}</b>\n\n"
        f"Приз: {html_esc(prize)}\n"
        f"Победителей: {winners}\n"
        f"До конца: {format_time(seconds)}\n\n"
        f"Жми кнопку, чтобы участвовать."
    )
    msg = await message.answer(text, reply_markup=g_kb(gid))
    await set_giveaway_message(gid, msg.message_id)
    try:
        await message.delete()
    except Exception:
        pass


@router.callback_query(F.data.startswith("gjoin:"))
async def cb_join(callback: CallbackQuery):
    gid = int(callback.data.split(":")[1])
    g = await get_giveaway(gid)
    if not g or g["closed"]:
        await callback.answer("Розыгрыш уже завершён.", show_alert=True)
        return
    if g["chat_id"] != callback.message.chat.id:
        await callback.answer("Не тот чат.", show_alert=True)
        return
    ok = await join_giveaway(gid, callback.from_user.id)
    members = await giveaway_members(gid)
    await callback.answer("Ты в деле!" if ok else "Ты уже участвуешь.")
    if ok:
        try:
            text = callback.message.html_text or callback.message.text or ""
            # keep original, append count
            base = text.split("\n\nУчастников:")[0]
            await callback.message.edit_text(
                base + f"\n\nУчастников: {len(members)}",
                reply_markup=g_kb(gid),
            )
        except Exception:
            pass


@router.message(Command("gend"), IsAdminFilter(), IsGroupFilter())
async def cmd_gend(message: Message, bot: Bot, command: CommandObject):
    if not command.args or not command.args.strip().isdigit():
        await message.reply("/gend ID")
        return
    await finish_giveaway(bot, int(command.args.strip()), force=True)


async def finish_giveaway(bot: Bot, gid: int, force: bool = False):
    g = await get_giveaway(gid)
    if not g or g["closed"]:
        return
    await close_giveaway(gid)
    members = await giveaway_members(gid)
    if not members:
        await bot.send_message(g["chat_id"], f"Розыгрыш #{gid} завершён без участников.")
        return
    k = min(g["winners"], len(members))
    winners = random.sample(members, k)
    names = ", ".join(f"<code>{uid}</code>" for uid in winners)
    await bot.send_message(
        g["chat_id"],
        f"🏆 <b>Итоги розыгрыша #{gid}</b>\nПриз: {html_esc(g['prize'])}\nПобедители: {names}",
    )
