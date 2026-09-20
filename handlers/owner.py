from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from filters.admin import IsOwnerFilter
from core.text import mention, html_esc
from database.db import gban_user, ungban_user, list_gbans, list_chats, count_chats
from handlers.common import resolve_user
from services.logger import send_log
from config import config

router = Router()
router.message.filter(IsOwnerFilter())


@router.message(Command("gban"))
async def cmd_gban(message: Message, bot: Bot, command: CommandObject):
    user, rest = await resolve_user(message, bot, command.args or "")
    if not user:
        await message.reply("Укажи пользователя.")
        return
    reason = rest or "Global ban"
    await gban_user(user.id, message.from_user.id, reason)
    chats = await list_chats()
    ok = 0
    for c in chats:
        try:
            await bot.ban_chat_member(c["chat_id"], user.id)
            ok += 1
        except Exception:
            pass
    await message.reply(f"GBAN {mention(user)}\n{html_esc(reason)}\nЧатов: {ok}/{len(chats)}")


@router.message(Command("ungban"))
async def cmd_ungban(message: Message, bot: Bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    if not user:
        return
    await ungban_user(user.id)
    for c in await list_chats():
        try:
            await bot.unban_chat_member(c["chat_id"], user.id, only_if_banned=True)
        except Exception:
            pass
    await message.reply(f"Снят gban с {mention(user)}")


@router.message(Command("gbanlist"))
async def cmd_gbanlist(message: Message):
    rows = await list_gbans()
    if not rows:
        await message.reply("Пусто.")
        return
    await message.reply("\n".join(f"<code>{r['user_id']}</code> — {html_esc(r.get('reason'))}" for r in rows[:50]))


@router.message(Command("leave"))
async def cmd_leave(message: Message, bot: Bot, command: CommandObject):
    cid = int(command.args.strip()) if command.args and command.args.strip().lstrip("-").isdigit() else message.chat.id
    await bot.leave_chat(cid)
    if message.chat.id != cid:
        await message.reply("Вышел.")


@router.message(Command("chatlist"))
async def cmd_chatlist(message: Message):
    chats = await list_chats()
    lines = [f"{c.get('title')} <code>{c['chat_id']}</code>" for c in chats[:80]]
    await message.reply(f"Чатов: {len(chats)}\n" + "\n".join(lines))


@router.message(Command("broadcast"))
async def cmd_broadcast(message: Message, bot: Bot, command: CommandObject):
    text = command.args or (message.reply_to_message.text if message.reply_to_message else None)
    if not text:
        await message.reply("/broadcast текст")
        return
    chats = await list_chats()
    ok = fail = 0
    for c in chats:
        try:
            await bot.send_message(c["chat_id"], text)
            ok += 1
        except Exception:
            fail += 1
    await message.reply(f"Ок {ok}, ошибок {fail}")


@router.message(Command("botstats"))
async def cmd_botstats(message: Message):
    n = await count_chats()
    await message.reply(f"{config.BOT_NAME} {config.VERSION}\nЧатов: {n}\nВладельцев: {len(config.ADMINS)}")


@router.message(Command("echo"))
async def cmd_echo(message: Message, command: CommandObject):
    await message.reply(command.args or "…")
