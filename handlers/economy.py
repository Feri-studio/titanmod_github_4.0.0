"""Simple economy — daily, balance, pay, top — TitanMod 4.0."""
from __future__ import annotations

from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import HR, ok, fail
from core.text import mention
from database.extra import get_balance, add_coins, claim_daily, economy_top
from handlers.common import resolve_user

router = Router()


@router.message(Command("daily", "день", "bonus"))
async def cmd_daily(message: Message):
    if message.chat.type == "private":
        await message.reply("🎁 Daily работает в группе. Или открой /menu → Экономика")
        return
    success, bal, streak = await claim_daily(message.chat.id, message.from_user.id)
    if success:
        await message.reply(
            ok(
                f"Ежедневная награда получена!\n"
                f"💰 Баланс: <b>{bal}</b>\n"
                f"🔥 Серия: <b>{streak}</b> дн."
            )
        )
    else:
        await message.reply(fail(f"Уже получал сегодня. Баланс: <b>{bal}</b> · серия {streak}"))


@router.message(Command("balance", "bal", "coins", "баланс", "монеты"))
async def cmd_balance(message: Message, command: CommandObject, bot: Bot):
    chat_id = message.chat.id
    if message.chat.type == "private":
        await message.reply("В ЛС открой /menu → Экономика. В группе: /balance")
        return
    target, _ = await resolve_user(message, bot, command.args or "")
    user = target or message.from_user
    bal = await get_balance(chat_id, user.id)
    who = "Твой" if user.id == message.from_user.id else mention(user)
    await message.reply(f"💰 {who} баланс: <b>{bal}</b> монет")


@router.message(Command("pay", "transfer", "дать", "перевести"))
async def cmd_pay(message: Message, command: CommandObject, bot: Bot):
    if message.chat.type == "private":
        return
    target, rest = await resolve_user(message, bot, command.args or "")
    if not target:
        await message.reply(
            "Ответь на сообщение пользователя и укажи сумму:\n"
            "<code>/pay 100</code>\n"
            "Или: <code>/pay 123456789 100</code>"
        )
        return
    parts = (rest or "").split()
    if not parts or not parts[0].lstrip("-").isdigit():
        await message.reply("Укажи сумму: <code>/pay 50</code>")
        return
    amount = int(parts[0])
    if amount <= 0:
        await message.reply(fail("Сумма должна быть > 0"))
        return
    if target.id == message.from_user.id:
        await message.reply(fail("Нельзя перевести себе"))
        return
    bal = await get_balance(message.chat.id, message.from_user.id)
    if bal < amount:
        await message.reply(fail(f"Недостаточно средств (есть {bal})"))
        return
    await add_coins(message.chat.id, message.from_user.id, -amount)
    await add_coins(message.chat.id, target.id, amount)
    await message.reply(ok(f"Переведено <b>{amount}</b> монет → {mention(target)}"))


@router.message(Command("topcoins", "baltop", "топмонет"))
async def cmd_topcoins(message: Message):
    if message.chat.type == "private":
        return
    rows = await economy_top(message.chat.id, 10)
    if not rows:
        await message.reply("Пока пусто. Получи /daily")
        return
    lines = ["💰 <b>Топ монет</b>", HR]
    medals = ["🥇", "🥈", "🥉"]
    for i, r in enumerate(rows):
        med = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{med} <code>{r['user_id']}</code> — <b>{r['balance']}</b>")
    await message.reply("\n".join(lines))


@router.message(Command("addcoins", "givemoney"))
async def cmd_addcoins(message: Message, command: CommandObject, bot: Bot):
    from config import config
    from handlers.ranks import effective_rank

    if message.chat.type == "private":
        return
    level = await effective_rank(bot, message.chat.id, message.from_user.id)
    if level < 5 and not config.is_owner(message.from_user.id):
        await message.reply(fail("Нужен ранг Админ+"))
        return
    target, rest = await resolve_user(message, bot, command.args or "")
    if not target:
        await message.reply("Укажи пользователя (ответом или id) и сумму")
        return
    parts = (rest or "").split()
    if not parts or not parts[0].lstrip("-").isdigit():
        await message.reply("<code>/addcoins 123456789 100</code>")
        return
    amount = int(parts[0])
    new_bal = await add_coins(message.chat.id, target.id, amount)
    await message.reply(ok(f"{mention(target)} теперь <b>{new_bal}</b> монет"))
