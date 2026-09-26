"""Extra mini-games, RF law snippets, utilities — TitanMod 4.8."""
from __future__ import annotations

import hashlib
import random
import secrets
import string
import time
import uuid
from datetime import datetime, timezone

from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command, CommandObject

from core.style import card, ok, fail, HR_LIGHT
from core.text import html_esc

# Lazy loaders — не тормозят старт бота на 100k+ строк
_cache: dict = {}

def _bulk():
    if "bulk" not in _cache:
        try:
            from data_bulk import WORDS, FACTS, TRIVIA, PHRASES, BALL_ANSWERS, LAW_INDEX
            _cache["bulk"] = (WORDS, FACTS, TRIVIA, PHRASES, BALL_ANSWERS, LAW_INDEX)
        except Exception:
            _cache["bulk"] = ([], [], [], [], [], {})
    return _cache["bulk"]

def _games():
    if "games" not in _cache:
        try:
            from data_games import HANG_WORDS, BJ_LINES, ACHIEVEMENTS, TRIVIA_MEGA, RPS_TAUNTS
            _cache["games"] = (HANG_WORDS, BJ_LINES, ACHIEVEMENTS, TRIVIA_MEGA, RPS_TAUNTS)
        except Exception:
            _cache["games"] = ([], [], [], [], [])
    return _cache["games"]


router = Router()

# ── popular RF code snippets (кратко, справочно) ─────────────────
UK_RF = {
    105: ("Убийство", "Умышленное причинение смерти другому человеку — ст. 105 УК РФ."),
    111: ("Тяжкий вред здоровью", "Умышленное причинение тяжкого вреда здоровью — ст. 111 УК РФ."),
    158: ("Кража", "Тайное хищение чужого имущества — ст. 158 УК РФ."),
    159: ("Мошенничество", "Хищение путём обмана или злоупотребления доверием — ст. 159 УК РФ."),
    161: ("Грабёж", "Открытое хищение чужого имущества — ст. 161 УК РФ."),
    162: ("Разбой", "Нападение в целях хищения с применением насилия — ст. 162 УК РФ."),
    163: ("Вымогательство", "Требование передачи имущества под угрозой — ст. 163 УК РФ."),
    167: ("Уничтожение имущества", "Умышленные уничтожение или повреждение чужого имущества — ст. 167 УК РФ."),
    228: ("Наротические средства", "Незаконные приобретение, хранение и т.п. наркотических средств — ст. 228 УК РФ."),
    264: ("ПДД / транспорт", "Нарушение ПДД и эксплуатация ТС — ст. 264 УК РФ."),
    282: ("Возбуждение ненависти", "Возбуждение ненависти либо вражды — ст. 282 УК РФ."),
    327: ("Подделка документов", "Подделка, изготовление или оборот поддельных документов — ст. 327 УК РФ."),
}

KOAP_RF = {
    6.1: ("Побои", "Побои — ст. 6.1.1 КоАП РФ (административная ответственность в ряде случаев)."),
    12.7: ("Управление без прав", "Управление ТС водителем, не имеющим права управления — ст. 12.7 КоАП РФ."),
    12.9: ("Превышение скорости", "Превышение установленной скорости движения — ст. 12.9 КоАП РФ."),
    12.26: ("Отказ от освидетельствования", "Невыполнение требования о прохождении медосвидетельствования — ст. 12.26 КоАП РФ."),
    20.1: ("Мелкое хулиганство", "Мелкое хулиганство — ст. 20.1 КоАП РФ."),
    20.20: ("Распитие в запрещённых местах", "Распитие алкоголя в запрещённых местах — ст. 20.20 КоАП РФ."),
}

FACTS_RU = [
    "Байкал — самое глубокое озеро в мире.",
    "Транссиб — одна из самых длинных железных дорог на планете.",
    "В России 11 часовых поясов.",
    "Мамаев курган и «Родина-мать» — символы Волгограда.",
    "Эрмитаж в Санкт-Петербурге — один из крупнейших музеев мира.",
    "Красная площадь внесена в список наследия ЮНЕСКО.",
    "Вулканы Камчатки — объект всемирного наследия.",
    "Россия омывается водами трёх океанов.",
]

COMPLIMENTS = [
    "Ты сегодня на высоте.",
    "С тобой чат становится добрее.",
    "У тебя отличное чувство такта.",
    "Ты умеешь поддержать — это ценно.",
    "Твоя энергия заряжает окружающих.",
]

EIGHT = [
    "Да.", "Нет.", "Скорее да.", "Скорее нет.", "Спроси позже.",
    "Точно да!", "Даже не думай.", "Шансы есть.", "Сомнительно.",
]


_hang: dict[int, dict] = {}
_bj: dict[int, dict] = {}


def _draw_hang(word: str, guessed: set[str]) -> str:
    shown = " ".join(c if c in guessed else "_" for c in word)
    return shown


@router.message(Command("hangman", "виселица"))
async def cmd_hangman(message: Message, command: CommandObject):
    uid = message.from_user.id if message.from_user else 0
    arg = (command.args or "").strip().lower()
    HANG_WORDS, BJ_LINES, ACHIEVEMENTS, TRIVIA_MEGA, RPS_TAUNTS = _games()
    BULK_WORDS, BULK_FACTS, BULK_TRIVIA, PHRASES, BALL_ANSWERS, LAW_INDEX = _bulk()
    words = list(HANG_WORDS[:2000]) if HANG_WORDS else (list(BULK_WORDS[:500]) if BULK_WORDS else [
        "телеграм", "модерация", "конституция", "федерация", "алгоритм",
        "безопасность", "сообщество", "клавиатура", "сообщение", "администратор",
    ])
    if arg in ("new", "новая", "start", "") and (arg != "" or uid not in _hang):
        if arg in ("new", "новая", "start", "") and uid not in _hang:
            pass
        if arg in ("new", "новая", "start") or uid not in _hang:
            w = random.choice(words)
            _hang[uid] = {"word": w, "guessed": set(), "hp": 7}
            await message.reply(
                card(
                    "Виселица",
                    f"{_draw_hang(w, set())}\nЖизни: <b>7</b>\nПиши: <code>/hangman а</code>",
                    emoji="🪢",
                )
            )
            return
    if uid not in _hang:
        await message.reply(fail("Начни: <code>/hangman new</code>"))
        return
    if not arg or len(arg) != 1 or not arg.isalpha():
        st = _hang[uid]
        await message.reply(
            card(
                "Виселица",
                f"{_draw_hang(st['word'], st['guessed'])}\n"
                f"Жизни: <b>{st['hp']}</b> · буквы: {''.join(sorted(st['guessed'])) or '—'}",
                emoji="🪢",
            )
        )
        return
    st = _hang[uid]
    letter = arg[0]
    if letter in st["guessed"]:
        await message.reply(fail("Эта буква уже была."))
        return
    st["guessed"].add(letter)
    if letter not in st["word"]:
        st["hp"] -= 1
    shown = _draw_hang(st["word"], st["guessed"])
    if all(c in st["guessed"] for c in st["word"]):
        del _hang[uid]
        await message.reply(ok(f"Слово: <b>{html_esc(st['word'])}</b> — победа!"))
        return
    if st["hp"] <= 0:
        w = st["word"]
        del _hang[uid]
        await message.reply(fail(f"Проигрыш. Слово было: <b>{html_esc(w)}</b>"))
        return
    await message.reply(
        card("Виселица", f"{shown}\nЖизни: <b>{st['hp']}</b>", emoji="🪢")
    )


def _hand_val(cards: list[int]) -> int:
    s = sum(cards)
    # soft aces as 1 already; treat 11 if present as ace optional - keep simple 1-10
    return s


@router.message(Command("bj", "21", "blackjack"))
async def cmd_bj(message: Message, command: CommandObject):
    uid = message.from_user.id if message.from_user else 0
    arg = (command.args or "").strip().lower()
    if arg in ("new", "start", "новая", ""):
        if arg or uid not in _bj:
            a, b = random.randint(1, 11), random.randint(1, 11)
            _bj[uid] = {"cards": [a, b]}
            s = sum(_bj[uid]["cards"])
            await message.reply(
                card(
                    "21",
                    f"Карты: <b>{a}</b> + <b>{b}</b> = <b>{s}</b>\n"
                    f"Ещё: <code>/bj hit</code> · хватит: <code>/bj stand</code>",
                    emoji="🃏",
                )
            )
            return
    if uid not in _bj:
        await message.reply(fail("Начни: <code>/bj new</code>"))
        return
    st = _bj[uid]
    if arg in ("hit", "ещё", "еще", "h"):
        st["cards"].append(random.randint(1, 11))
        s = sum(st["cards"])
        cards = " + ".join(str(c) for c in st["cards"])
        if s > 21:
            del _bj[uid]
            await message.reply(fail(f"{cards} = <b>{s}</b> — перебор."))
            return
        await message.reply(card("21", f"{cards} = <b>{s}</b>\n<code>/bj hit</code> · <code>/bj stand</code>", emoji="🃏"))
        return
    if arg in ("stand", "стоп", "s"):
        s = sum(st["cards"])
        dealer = random.randint(17, 23)
        del _bj[uid]
        if dealer > 21 or s > dealer:
            res = "Ты выиграл"
        elif s == dealer:
            res = "Ничья"
        else:
            res = "Дилер выиграл"
        await message.reply(
            card("21", f"Ты: <b>{s}</b> · дилер: <b>{dealer}</b>\n<b>{res}</b>", emoji="🃏")
        )
        return
    await message.reply(fail("Команды: <code>/bj new</code> · <code>/bj hit</code> · <code>/bj stand</code>"))


@router.message(Command("uk", "ук"))
async def cmd_uk(message: Message, command: CommandObject):
    arg = (command.args or "").strip()
    if not arg:
        nums = ", ".join(str(k) for k in sorted(UK_RF.keys()))
        await message.reply(
            card(
                "УК РФ · краткие справки",
                f"Пример: <code>/ук 158</code>\nНомера в боте: {nums}\n"
                f"<i>Не юридическая консультация</i>",
                emoji="⚖️",
            )
        )
        return
    if not arg.isdigit() or int(arg) not in UK_RF:
        await message.reply(fail("Нет в подборке. Список: <code>/ук</code>"))
        return
    n = int(arg)
    title, text = UK_RF[n]
    await message.reply(card(f"УК РФ · ст. {n} · {title}", html_esc(text), emoji="⚖️", footer="Справочно · /ук"))


@router.message(Command("koap", "коап"))
async def cmd_koap(message: Message, command: CommandObject):
    arg = (command.args or "").strip().replace(",", ".")
    if not arg:
        nums = ", ".join(str(k) for k in sorted(KOAP_RF.keys()))
        await message.reply(
            card("КоАП РФ · справки", f"Пример: <code>/коап 12.9</code>\nЕсть: {nums}", emoji="📋")
        )
        return
    try:
        key = float(arg) if "." in arg else int(arg)
    except ValueError:
        await message.reply(fail("Формат: <code>/коап 12.9</code>"))
        return
    # normalize keys
    found = None
    for k in KOAP_RF:
        if float(k) == float(key) or str(k) == str(arg):
            found = k
            break
    if found is None:
        await message.reply(fail("Нет в подборке. <code>/коап</code>"))
        return
    title, text = KOAP_RF[found]
    await message.reply(card(f"КоАП · ст. {found} · {title}", html_esc(text), emoji="📋", footer="Справочно"))


@router.message(Command("fact", "факт"))
async def cmd_fact(message: Message):
    _, BULK_FACTS, *___ = _bulk()
    pool = BULK_FACTS or FACTS_RU
    await message.reply(card("Факт", random.choice(pool), emoji="📌"))


@router.message(Command("random", "rnd"))
async def cmd_random(message: Message, command: CommandObject):
    arg = (command.args or "1-100").strip().replace(" ", "")
    try:
        if "-" in arg:
            a, b = arg.split("-", 1)
            lo, hi = int(a), int(b)
        else:
            lo, hi = 1, int(arg)
        if lo > hi:
            lo, hi = hi, lo
        hi = min(hi, 10**9)
        n = random.randint(lo, hi)
        await message.reply(card("Случайное", f"От {lo} до {hi}: <b>{n}</b>", emoji="🎲"))
    except Exception:
        await message.reply(fail("Формат: <code>/random 1-100</code>"))


@router.message(Command("extras", "допы", "ещё"))
async def cmd_extras_help(message: Message):
    await message.reply(
        card(
            "Ещё функции",
            "\n".join([
                "<b>Игры</b> — /hangman /bj /rps /guess /roulette /trivia",
                "<b>Право РФ</b> — /статья /статьи /ук /коап",
                "<b>Утилиты</b> — /password /uuid /hash /time /random",
                "<b>Фан</b> — /fact /compliment /ball",
                "",
                "Список игр: /minigames",
            ]),
            emoji="✨",
            footer="TitanMod · /extras",
        )
    )


@router.message(Command("bulkstats", "базаконтента"))
async def cmd_bulkstats(message: Message):
    BULK_WORDS, BULK_FACTS, BULK_TRIVIA, PHRASES, BALL_ANSWERS, LAW_INDEX = _bulk()
    HANG_WORDS, BJ_LINES, ACHIEVEMENTS, TRIVIA_MEGA, RPS_TAUNTS = _games()
    body = "\n".join([
        f"Слова bulk: <b>{len(BULK_WORDS)}</b>",
        f"Факты: <b>{len(BULK_FACTS)}</b>",
        f"Викторина bulk: <b>{len(BULK_TRIVIA)}</b>",
        f"Игры trivia mega: <b>{len(TRIVIA_MEGA)}</b>",
        f"Hang words: <b>{len(HANG_WORDS)}</b>",
        f"RPS taunts: <b>{len(RPS_TAUNTS)}</b>",
        f"Достижения: <b>{len(ACHIEVEMENTS)}</b>",
        f"Право-индекс: <b>{len(LAW_INDEX)}</b>",
    ])
    await message.reply(card("База контента", body, emoji="📦", footer="lazy-load · data_bulk + data_games"))
