"""TitanMod 4.2 — shop, rob, coinflip, status, cleanup."""
from __future__ import annotations

import random
import time

from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import card, ok, fail, HR
from core.text import html_esc, mention
from core.ranks import effective_rank, rank_badge
from filters.rank import RankOrAdminFilter
from database.extra import (
    get_balance,
    add_coins,
    check_cooldown,
    set_cooldown,
    inv_add, inv_has,
)

router = Router()

SHOP = {
    "vip": (500, "VIP-статус (локальная отметка)"),
    "shield": (200, "Щит от /rob на 1 час"),
    "lootbox": (100, "Случайные 50–150 монет"),
    "title": (300, "Титул через /setrank"),
}

_shields: dict[tuple[int, int], float] = {}


@router.message(Command("shop", "магазин"))
async def cmd_shop(message: Message):
    if message.chat.type == "private":
        await message.reply("Магазин работает в группе.")
        return
    lines = ["🛒 <b>Магазин</b>", HR]
    for k, (price, desc) in SHOP.items():
        lines.append(f"• <code>{k}</code> — <b>{price}</b> · {desc}")
    lines.append(HR)
    lines.append("Купить: <code>/buy lootbox</code>")
    await message.reply("\n".join(lines))


@router.message(Command("buy", "купить"))
async def cmd_buy(message: Message, command: CommandObject):
    if message.chat.type == "private":
        return
    item = (command.args or "").strip().lower().split()[0] if command.args else ""
    if item not in SHOP:
        await message.reply(fail("Нет такого товара. /shop"))
        return
    price, desc = SHOP[item]
    bal = await get_balance(message.chat.id, message.from_user.id)
    if bal < price:
        await message.reply(fail(f"Нужно {price}, есть {bal}"))
        return
    await add_coins(message.chat.id, message.from_user.id, -price)
    if item == "lootbox":
        gain = random.randint(50, 150)
        bal = await add_coins(message.chat.id, message.from_user.id, gain)
        await message.reply(ok(f"Лутбокс: +<b>{gain}</b> · баланс <b>{bal}</b>"))
    elif item == "shield":
        exp = time.time() + 3600
        await inv_add(message.chat.id, message.from_user.id, "shield", 1, exp)
        _shields[(message.chat.id, message.from_user.id)] = exp
        bal = await get_balance(message.chat.id, message.from_user.id)
        await message.reply(ok(f"Щит на 1 час (в инвентаре). Баланс <b>{bal}</b>"))
    elif item == "vip":
        exp = time.time() + 7 * 86400
        await inv_add(message.chat.id, message.from_user.id, "vip", 1, exp)
        bal = await get_balance(message.chat.id, message.from_user.id)
        await message.reply(ok(f"VIP на 7 дней. Баланс <b>{bal}</b>"))
    else:
        await inv_add(message.chat.id, message.from_user.id, item, 1, 0)
        bal = await get_balance(message.chat.id, message.from_user.id)
        await message.reply(ok(f"Куплено <b>{item}</b>. {desc}. Баланс <b>{bal}</b>"))


@router.message(Command("rob", "ограбить"))
async def cmd_rob(message: Message, bot: Bot):
    if message.chat.type == "private":
        return
    ok_cd, left = await check_cooldown(message.chat.id, message.from_user.id, "rob", 600)
    if not ok_cd:
        await message.reply(fail(f"Ограбление через {left}с"))
        return
    if not message.reply_to_message or not message.reply_to_message.from_user:
        await message.reply("Ответь на сообщение жертвы: /rob")
        return
    target = message.reply_to_message.from_user
    if target.id == message.from_user.id:
        await message.reply(fail("Себя нельзя"))
        return
    if _shields.get((message.chat.id, target.id), 0) > time.time() or await inv_has(message.chat.id, target.id, "shield"):
        await message.reply(fail("У цели активен щит"))
        return
    tbal = await get_balance(message.chat.id, target.id)
    if tbal < 20:
        await message.reply(fail("У цели почти пусто"))
        return
    await set_cooldown(message.chat.id, message.from_user.id, "rob")
    if random.random() < 0.4:
        loss = random.randint(10, 30)
        bal = await add_coins(message.chat.id, message.from_user.id, -loss)
        await message.reply(fail(f"Неудача, штраф −{loss}. Баланс <b>{bal}</b>"))
        return
    steal = min(tbal, random.randint(10, max(15, tbal // 5)))
    await add_coins(message.chat.id, target.id, -steal)
    bal = await add_coins(message.chat.id, message.from_user.id, steal)
    await message.reply(ok(f"Украдено <b>{steal}</b> у {mention(target)}. Баланс <b>{bal}</b>"))


@router.message(Command("coinflip", "flip", "монетка"))
async def cmd_coinflip(message: Message, command: CommandObject):
    if message.chat.type == "private":
        return
    parts = (command.args or "").split()
    if not parts or not parts[0].isdigit():
        await message.reply("<code>/coinflip 20</code> — ставка")
        return
    bet = int(parts[0])
    if bet <= 0:
        return
    bal = await get_balance(message.chat.id, message.from_user.id)
    if bal < bet:
        await message.reply(fail(f"Нужно {bet}, есть {bal}"))
        return
    await add_coins(message.chat.id, message.from_user.id, -bet)
    if random.random() < 0.5:
        bal = await add_coins(message.chat.id, message.from_user.id, bet * 2)
        await message.reply(ok(f"Орёл! +{bet} · баланс <b>{bal}</b>"))
    else:
        bal = await get_balance(message.chat.id, message.from_user.id)
        await message.reply(fail(f"Решка. −{bet} · баланс <b>{bal}</b>"))


@router.message(Command("mystatus", "statusme", "мойстатус"))
async def cmd_mystatus(message: Message, bot: Bot):
    if message.chat.type == "private":
        await message.reply("В группе: /mystatus")
        return
    lvl = await effective_rank(bot, message.chat.id, message.from_user.id)
    bal = await get_balance(message.chat.id, message.from_user.id)
    await message.reply(
        card(
            "Статус",
            f"{rank_badge(lvl)}\nУровень ранга: <code>{lvl}</code>\n💰 Баланс: <b>{bal}</b>",
            emoji="🪪",
        )
    )


@router.message(Command("botstatus", "pingbot"))
async def cmd_botstatus(message: Message):
    from config import config as cfg

    await message.reply(
        card(
            "TitanMod",
            f"Версия: <b>{cfg.VERSION}</b>\nСтатус: online",
            emoji="🤖",
        )
    )


@router.message(Command("cleanup"), RankOrAdminFilter("purge"))
async def cmd_cleanup(message: Message, command: CommandObject):
    deleted = 0
    if message.reply_to_message:
        try:
            await message.reply_to_message.delete()
            deleted = 1
        except Exception:
            pass
    await message.reply(ok(f"Удалено: {deleted}. Массово: /purge"))


@router.message(Command("help42", "чтонового"))
async def cmd_help42(message: Message):
    await message.reply(
        card(
            "TitanMod 4.2",
            "• Ранги в /ban /mute /warn\n"
            "• /shop /buy /rob /coinflip\n"
            "• Кулдауны work/crime/slots\n"
            "• /mystatus /botstatus\n"
            "• /ticket · /menu · /rules · /stafflist",
            emoji="✨",
            footer="Список: /commands",
        )
    )


@router.message(Command("echo"))
async def cmd_echo(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    if not text:
        await message.reply("<code>/echo текст</code>")
        return
    await message.reply(html_esc(text[:3500]))


@router.message(Command("len", "length"))
async def cmd_len(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    if not text:
        await message.reply("<code>/len текст</code>")
        return
    await message.reply(
        card("Длина", f"Символов: <b>{len(text)}</b>\nСлов: <b>{len(text.split())}</b>", emoji="📏")
    )


@router.message(Command("reverse"))
async def cmd_reverse(message: Message, command: CommandObject):
    text = (command.args or "").strip()
    if not text and message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text
    if not text:
        await message.reply("<code>/reverse текст</code>")
        return
    await message.reply(html_esc(text[::-1][:3500]))
