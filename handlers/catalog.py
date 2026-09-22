"""Beautiful paginated command catalog: /commands /help extras."""
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from aiogram.filters import Command, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.commands import COMMANDS, CATEGORIES, HELP_TEXT, ALL_COMMAND_NAMES
from core.style import HR, HR_LIGHT, CAT_EMOJI, card, safe_edit
from core.text import html_esc

router = Router()
PAGE = 12

PUBLIC_MENU = [
    ("menu", "Личный кабинет"),
    ("commands", "Каталог всех команд"),
    ("help", "Справка по разделам"),
    ("settings", "Настройки чата"),
    ("ranks", "Система рангов"),
    ("rules", "Правила"),
    ("id", "ID чата и пользователя"),
    ("info", "Профиль пользователя"),
    ("stafflist", "Штат чата"),
    ("daily", "Ежедневная награда"),
    ("xp", "Уровень активности"),
    ("ping", "Проверка бота"),
]


def _items(cat: str | None = None, query: str | None = None):
    q = (query or "").lower().strip().lstrip("/")
    out = []
    for cmd, c, desc in COMMANDS:
        if cat and c != cat:
            continue
        if q and q not in cmd.lower() and q not in desc.lower() and q not in c:
            continue
        out.append((cmd, c, desc))
    return out


def catalog_kb(cat: str, page: int, total: int, query: str = "") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    pages = max(1, (total + PAGE - 1) // PAGE)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="«", callback_data=f"cmds:{cat}:{page-1}"))
    nav.append(InlineKeyboardButton(text=f"{page+1}/{pages}", callback_data="cmds:noop"))
    if page + 1 < pages:
        nav.append(InlineKeyboardButton(text="»", callback_data=f"cmds:{cat}:{page+1}"))
    if nav:
        b.row(*nav)

    row = []
    cats = [("all", "Все")] + [(k, v.split()[0] if v else k) for k, v in CATEGORIES.items()]
    labels = {
        "all": "📚 Все",
        "punish": "🔨 Бан",
        "warns": "⚠️ Варн",
        "locks": "🔒 Замки",
        "welcome": "👋 Вход",
        "notes": "📝 Заметки",
        "filters": "🔎 Фильтры",
        "fed": "🕸 Фед",
        "sec": "🛡 Сек",
        "admin": "⚙️ Админ",
        "ranks": "🏅 Ранги",
        "economy": "💰 Эко",
        "cabinet": "🏠 ЛК",
        "tickets": "🎫 Тикеты",
        "xp": "✨ XP",
        "info": "ℹ️ Инфо",
        "util": "🧰 Утил",
        "fun": "🎮 Fun",
        "owner": "👑 Owner",
    }
    for key, _ in cats:
        mark = "· " if key == cat else ""
        title = labels.get(key, key)
        row.append(InlineKeyboardButton(text=f"{mark}{title}", callback_data=f"cmds:{key}:0"))
        if len(row) == 3:
            b.row(*row)
            row = []
    if row:
        b.row(*row)
    b.row(InlineKeyboardButton(text="✖ Закрыть", callback_data="cmds:close"))
    return b.as_markup()


def render_page(cat: str, page: int, query: str = "") -> tuple[str, InlineKeyboardMarkup]:
    items = _items(None if cat in ("all", "") else cat, query or None)
    total = len(items)
    start = page * PAGE
    chunk = items[start:start + PAGE]
    title = "Все команды" if cat in ("all", "") else CATEGORIES.get(cat, cat)
    em = CAT_EMOJI.get(cat, "📚")
    lines = [
        f"{em} <b>{html_esc(title)}</b>",
        f"<i>TitanMod {config.VERSION} · {len(ALL_COMMAND_NAMES)} команд</i>",
        HR,
    ]
    if query:
        lines.append(f"Поиск: <code>{html_esc(query)}</code> · {total} шт.")
        lines.append(HR)
    if not chunk:
        lines.append("Ничего не нашлось. Попробуй <code>/commands ban</code>")
    else:
        for cmd, c, desc in chunk:
            e = CAT_EMOJI.get(c, "•")
            lines.append(f"{e} <code>/{html_esc(cmd)}</code> — {html_esc(desc)}")
    lines.append(HR)
    lines.append("Подсказка: <code>/commands мут</code> или <code>/commands punish</code>")
    text = "\n".join(lines)
    if len(text) > 3900:
        text = text[:3890] + "…"
    return text, catalog_kb(cat or "all", page, total, query)


@router.message(Command("commands", "команды", "cmdlist", "commandlist"))
async def cmd_commands(message: Message, command: CommandObject):
    arg = (command.args or "").strip()
    cat, query, page = "all", "", 0
    if arg:
        key = arg.split()[0].lower().lstrip("/")
        if key in CATEGORIES:
            cat = key
            rest = arg[len(arg.split()[0]):].strip()
            query = rest
        else:
            query = arg
            cat = "all"
    text, kb = render_page(cat, page, query)
    await message.reply(text, reply_markup=kb, disable_web_page_preview=True)


@router.callback_query(F.data.startswith("cmds:"))
async def cmds_cb(callback: CallbackQuery):
    parts = callback.data.split(":")
    action = parts[1] if len(parts) > 1 else "all"
    if action == "close":
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.answer()
        return
    if action == "noop":
        await callback.answer()
        return
    cat = action
    page = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    text, kb = render_page(cat, page, "")
    await safe_edit(callback.message, text, kb)
    await callback.answer()


async def setup_bot_commands(bot: Bot):
    cmds = [BotCommand(command=c, description=d[:80]) for c, d in PUBLIC_MENU]
    try:
        await bot.set_my_commands(cmds)
    except Exception:
        pass
