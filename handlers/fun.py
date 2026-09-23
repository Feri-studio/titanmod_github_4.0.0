import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject
from core.text import mention, html_esc
from database.db import get_settings
from handlers.common import resolve_user

router = Router()

JOKES = [
    "Бот не банит — бот воспитывает.",
    "Если молчать 5 секунд, антифлуд считает тебя дзен-мастером.",
    "Админ всегда прав. Даже когда неправ — у него /mute.",
    "Капча отделяет людей от людей, которые забыли нажать кнопку.",
    "Федерация — это когда бан один, а чатов много.",
    "Я не слежу за чатом. Я просто живу в нём.",
    "Warn 1/3 — ещё друзья. Warn 3/3 — уже статистика.",
]
QUOTES = [
    "Порядок — это когда фильтры включены.",
    "Сначала правила, потом мемы.",
    "Тишина тоже контент.",
    "Мут лечит лучше, чем спор.",
]
BALL = ["Да", "Нет", "Возможно", "Спроси позже", "Точно да", "Точно нет", "50/50", "Звёзды говорят нет", "Сделай /mute и подумай"]


def _fun_ok(settings: dict | None) -> bool:
    if not settings:
        return True
    return bool(settings.get("fun_enabled", 1))


@router.message(Command("coin"))
async def cmd_coin(message: Message):
    await message.reply(random.choice(["Орёл", "Решка"]))


@router.message(Command("dice"))
async def cmd_dice(message: Message):
    await message.reply(f"Выпало: {random.randint(1, 6)}")


@router.message(Command("shrug"))
async def cmd_shrug(message: Message):
    await message.reply("¯\\_(ツ)_/¯")


@router.message(Command("tableflip"))
async def cmd_flip(message: Message):
    await message.reply("(╯°□°)╯︵ ┻━┻")


@router.message(Command("unflip"))
async def cmd_unflip(message: Message):
    await message.reply("┬─┬ ノ( ゜-゜ノ)")


@router.message(Command("clap"))
async def cmd_clap(message: Message, command: CommandObject):
    t = command.args or "clap"
    await message.reply(" 👏 ".join(t.split()))


@router.message(Command("mock"))
async def cmd_mock(message: Message, command: CommandObject):
    t = command.args or (message.reply_to_message.text if message.reply_to_message else "")
    if not t:
        return
    out = "".join(c.upper() if i % 2 else c.lower() for i, c in enumerate(t))
    await message.reply(html_esc(out))


@router.message(Command("vapor"))
async def cmd_vapor(message: Message, command: CommandObject):
    t = command.args or ""
    await message.reply("".join(chr(ord(c) + 0xFEE0) if 33 <= ord(c) <= 126 else c for c in t) or "Ｖ")


@router.message(Command("uwu"))
async def cmd_uwu(message: Message, command: CommandObject):
    t = (command.args or "hello").replace("r", "w").replace("l", "w").replace("R", "W").replace("L", "W")
    await message.reply(html_esc(t) + " uwu")


@router.message(Command("hug", "slap", "kiss", "pat"))
async def cmd_act(message: Message, bot, command: CommandObject):
    user, _ = await resolve_user(message, bot, command.args or "")
    target = mention(user) if user else "чат"
    verb = {"hug": "обнял", "slap": "шлёпнул", "kiss": "поцеловал", "pat": "погладил"}[command.command]
    await message.reply(f"{mention(message.from_user)} {verb} {target}")


@router.message(Command("rate"))
async def cmd_rate(message: Message, command: CommandObject):
    thing = command.args or "это"
    await message.reply(f"{html_esc(thing)} — {random.randint(0, 10)}/10")


@router.message(Command("ship"))
async def cmd_ship(message: Message, command: CommandObject):
    if not command.args or " " not in command.args:
        await message.reply("/ship А Б")
        return
    a, b = command.args.split(maxsplit=1)
    score = (sum(map(ord, a)) + sum(map(ord, b))) % 101
    await message.reply(f"{html_esc(a)} + {html_esc(b)} = {score}%")


@router.message(Command("ball"))
async def cmd_ball(message: Message, command: CommandObject):
    await message.reply(random.choice(BALL))


@router.message(Command("joke"))
async def cmd_joke(message: Message):
    await message.reply(random.choice(JOKES))


@router.message(Command("quote"))
async def cmd_quote(message: Message):
    await message.reply("«" + random.choice(QUOTES) + "»")

@router.message(Command("choose", "выбери"))
async def cmd_choose(message: Message, command: CommandObject):
    raw = (command.args or "").strip()
    if not raw:
        await message.reply("<code>/choose a | b | c</code>")
        return
    parts = [p.strip() for p in raw.replace(",", "|").split("|") if p.strip()]
    if len(parts) < 2:
        await message.reply("Нужно 2+ варианта")
        return
    import random
    from core.text import html_esc
    await message.reply(f"→ <b>{html_esc(random.choice(parts))}</b>")
