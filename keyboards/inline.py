from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from core.defaults import LOCK_TYPES


def settings_main_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="👋 Приветствия", callback_data=f"set:welcome:{chat_id}"),
        InlineKeyboardButton(text="🛡 Модерация", callback_data=f"set:moderation:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="⚡ Антифлуд", callback_data=f"set:flood:{chat_id}"),
        InlineKeyboardButton(text="⚠️ Варны", callback_data=f"set:warns:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🔒 Замки", callback_data=f"set:locks:{chat_id}"),
        InlineKeyboardButton(text="🔗 Фильтры", callback_data=f"set:filters:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🧪 Капча / рейд", callback_data=f"set:security:{chat_id}"),
        InlineKeyboardButton(text="📋 Логи", callback_data=f"set:logs:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="📜 Правила", callback_data=f"set:rules:{chat_id}"),
        InlineKeyboardButton(text="📊 Статистика", callback_data=f"set:stats:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🌙 Ночь", callback_data=f"set:night:{chat_id}"),
        InlineKeyboardButton(text="✨ Прочее", callback_data=f"set:extra:{chat_id}"),
    )
    b.row(InlineKeyboardButton(text="✖ Закрыть", callback_data="set:close"))
    return b.as_markup()


def back_kb(chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="← Назад", callback_data=f"set:main:{chat_id}"))
    return b.as_markup()


def toggle_kb(chat_id: int, items: list[tuple[str, str, bool]]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    row = []
    for key, label, enabled in items:
        mark = "✅" if enabled else "❌"
        row.append(InlineKeyboardButton(text=f"{mark} {label}", callback_data=f"tg:{key}:{chat_id}"))
        if len(row) == 2:
            b.row(*row)
            row = []
    if row:
        b.row(*row)
    b.row(InlineKeyboardButton(text="← Назад", callback_data=f"set:main:{chat_id}"))
    return b.as_markup()


def locks_kb(chat_id: int, enabled: set[str], page: int = 0) -> InlineKeyboardMarkup:
    keys = list(LOCK_TYPES.keys())
    chunk = 12
    start = page * chunk
    part = keys[start:start + chunk]
    b = InlineKeyboardBuilder()
    row = []
    for k in part:
        mark = "🔒" if k in enabled else "🔓"
        row.append(InlineKeyboardButton(text=f"{mark} {k}", callback_data=f"lockt:{k}:{chat_id}"))
        if len(row) == 2:
            b.row(*row)
            row = []
    if row:
        b.row(*row)
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="«", callback_data=f"set:locks:{chat_id}:{page-1}"))
    if start + chunk < len(keys):
        nav.append(InlineKeyboardButton(text="»", callback_data=f"set:locks:{chat_id}:{page+1}"))
    if nav:
        b.row(*nav)
    b.row(InlineKeyboardButton(text="← Назад", callback_data=f"set:main:{chat_id}"))
    return b.as_markup()


def captcha_kb(chat_id: int, user_id: int, mode: str, payload: str = "") -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if mode == "button":
        b.row(InlineKeyboardButton(text="✅ Я человек", callback_data=f"cpt:ok:{chat_id}:{user_id}"))
    elif mode == "emoji" and payload:
        for e in payload.split("|"):
            b.row(InlineKeyboardButton(text=e, callback_data=f"cpt:{e}:{chat_id}:{user_id}"))
    return b.as_markup()


def confirm_kb(action: str, user_id: int, chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"cfm:{action}:{user_id}:{chat_id}"),
        InlineKeyboardButton(text="✖ Нет", callback_data="cfm:cancel"),
    )
    return b.as_markup()


def help_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    cats = [
        ("punish", "🔨 Наказания"),
        ("warns", "⚠️ Варны"),
        ("locks", "🔒 Замки"),
        ("welcome", "👋 Вход"),
        ("notes", "📝 Заметки"),
        ("filters", "🔎 Фильтры"),
        ("fed", "🕸 Федерации"),
        ("sec", "🛡 Безопасность"),
        ("admin", "⚙️ Админы"),
        ("info", "ℹ️ Инфо"),
        ("util", "🧰 Утилиты"),
        ("fun", "🎮 Fun"),
        ("owner", "👑 Владелец"),
    ]
    row = []
    for key, label in cats:
        row.append(InlineKeyboardButton(text=label, callback_data=f"help:{key}"))
        if len(row) == 2:
            b.row(*row)
            row = []
    if row:
        b.row(*row)
    b.row(
        InlineKeyboardButton(text="📚 Каталог", callback_data="cmds:all:0"),
        InlineKeyboardButton(text="✖ Закрыть", callback_data="cmds:close"),
    )
    return b.as_markup()


def user_actions_kb(user_id: int, chat_id: int) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="⚠️ Варн", callback_data=f"act:warn:{user_id}:{chat_id}"),
        InlineKeyboardButton(text="🔇 Мут", callback_data=f"act:mute:{user_id}:{chat_id}"),
    )
    b.row(
        InlineKeyboardButton(text="🚫 Бан", callback_data=f"act:ban:{user_id}:{chat_id}"),
        InlineKeyboardButton(text="👢 Кик", callback_data=f"act:kick:{user_id}:{chat_id}"),
    )
    return b.as_markup()
