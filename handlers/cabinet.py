"""
Personal Cabinet / Menu in private messages — TitanMod 4.0.
When user opens the bot in DM they get a rich interactive menu.
"""
from __future__ import annotations

from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import config
from core.style import HR, HR_LIGHT, card, ok, fail, cabinet_header, safe_edit, safe_answer, progress_bar
from core.text import html_esc
from core.ranks import get_rank_info, rank_list_text
from database.db import get_connection
from database.extra import (
    get_user_prefs, set_user_pref, get_user_rank,
    get_balance, claim_daily, get_xp,
)

router = Router()


async def _safe_xp(chat_id: int, user_id: int) -> tuple[int, int]:
    try:
        row = await get_xp(chat_id, user_id)
        if row:
            return int(row.get("xp", 0)), int(row.get("level", 1))
    except Exception:
        pass
    return 0, 1


def main_menu_kb(is_connected: bool = False) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(
        InlineKeyboardButton(text="👤  Профиль", callback_data="cab:profile"),
        InlineKeyboardButton(text="🏅  Ранги", callback_data="cab:ranks"),
    )
    b.row(
        InlineKeyboardButton(text="🔗  Мои чаты", callback_data="cab:chats"),
        InlineKeyboardButton(text="⚙️  Настройки", callback_data="cab:settings"),
    )
    b.row(
        InlineKeyboardButton(text="📊  Статистика", callback_data="cab:stats"),
        InlineKeyboardButton(text="💰  Экономика", callback_data="cab:eco"),
    )
    b.row(
        InlineKeyboardButton(text="📚  Команды", callback_data="cab:cmds"),
        InlineKeyboardButton(text="❓  Справка", callback_data="cab:help"),
    )
    b.row(
        InlineKeyboardButton(text="🎫  Поддержка", callback_data="cab:support"),
        InlineKeyboardButton(text="ℹ️  О боте", callback_data="cab:about"),
    )
    b.row(
        InlineKeyboardButton(text="🎮  Мини-игры", callback_data="cab:games"),
    )
    if is_connected:
        b.row(InlineKeyboardButton(text="🔓  Отвязать чат", callback_data="cab:disconnect"))
    b.row(InlineKeyboardButton(text="✕  Закрыть", callback_data="cab:close"))
    return b.as_markup()


def back_main_kb() -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="‹  В главное меню", callback_data="cab:home"))
    return b.as_markup()


def settings_kb(prefs: dict) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    lang = prefs.get("lang", "ru")
    np = "✅" if prefs.get("notify_punish", 1) else "❌"
    nl = "✅" if prefs.get("notify_levelup", 1) else "❌"
    b.row(InlineKeyboardButton(
        text=f"🌐 Язык: {lang.upper()}",
        callback_data="cab:set:lang",
    ))
    b.row(InlineKeyboardButton(
        text=f"{np} Уведомления о наказаниях",
        callback_data="cab:set:notify_punish",
    ))
    b.row(InlineKeyboardButton(
        text=f"{nl} Уведомления об уровнях",
        callback_data="cab:set:notify_levelup",
    ))
    b.row(InlineKeyboardButton(text="‹  В главное меню", callback_data="cab:home"))
    return b.as_markup()


async def build_home_text(user, bot: Bot) -> tuple[str, bool]:
    name = user.first_name or "друг"
    conn = await get_connection(user.id)
    xp, level = 0, 1
    rank_level = 0
    if conn:
        xp, level = await _safe_xp(conn, user.id)
        rank_level = await get_user_rank(conn, user.id)
    if config.is_owner(user.id):
        rank_level = 7
    info = get_rank_info(rank_level)
    text = cabinet_header(name, f"{info.emoji} {info.name}", xp, level)
    text += (
        f"\nВыбери раздел ниже — всё управление ботом у тебя под рукой.\n"
        f"{HR_LIGHT}\n"
        f"<i>TitanMod {config.VERSION} · Личный кабинет</i>"
    )
    if conn:
        text += f"\n🔗 Привязан чат: <code>{conn}</code>"
    return text, bool(conn)


@router.message(Command("menu", "cabinet", "кабинет", "меню", "lk", "profile"))
async def cmd_menu(message: Message, bot: Bot):
    if message.chat.type != "private":
        await message.reply(
            "🏠 Личный кабинет доступен только в <b>личных сообщениях</b> бота.\n"
            "Напиши мне в ЛС: /menu"
        )
        return
    text, connected = await build_home_text(message.from_user, bot)
    await message.answer(text, reply_markup=main_menu_kb(connected), disable_web_page_preview=True)


@router.message(Command("start"), F.chat.type == "private")
async def cmd_start_private(message: Message, bot: Bot):
    """Enhanced /start in DM → open cabinet."""
    name = html_esc(message.from_user.first_name if message.from_user else "")
    me = await bot.get_me()
    add_url = f"https://t.me/{me.username}?startgroup=true" if me.username else None

    text = (
        f"✨ <b>{config.BOT_NAME}</b>  <code>v{config.VERSION}</code>\n"
        f"{HR}\n"
        f"Привет, <b>{name}</b>!\n\n"
        f"Модерация · ранги · экономика · тикеты · автомод\n\n"
        f"<b>Возможности</b>\n"
        f"› 🔨 Баны, муты, варны, карантин\n"
        f"› 🔒 Замки, антифлуд, антирейд\n"
        f"› 🏅 Штат рангов · XP · монеты\n"
        f"› 📜 Правила · капча · федерации\n"
        f"{HR}\n"
        f"<b>В группе</b>\n"
        f"1. Добавь бота <b>админом</b>\n"
        f"2. Права: удаление + блокировка участников\n"
        f"3. <code>/settings</code> · <code>/commands</code> · <code>/preset normal</code>\n"
        f"{HR_LIGHT}\n"
        f"Личное меню — кнопкой ниже 👇"
    )
    b = InlineKeyboardBuilder()
    b.row(InlineKeyboardButton(text="🏠  Личный кабинет", callback_data="cab:home"))
    if add_url:
        b.row(InlineKeyboardButton(text="➕ Добавить в группу", url=add_url))
    b.row(
        InlineKeyboardButton(text="📚 Команды", callback_data="cab:cmds"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="cab:about"),
    )
    await message.answer(text, reply_markup=b.as_markup(), disable_web_page_preview=True)


@router.callback_query(F.data.startswith("cab:"))
async def cabinet_cb(callback: CallbackQuery, bot: Bot):
    data = callback.data
    action = data.split(":", 1)[1]
    user = callback.from_user

    if action == "close":
        try:
            await callback.message.delete()
        except Exception:
            await safe_edit(callback.message, "меню закрыто")
        await safe_answer(callback)
        return

    if action == "home":
        text, connected = await build_home_text(user, bot)
        await safe_edit(callback.message, text, main_menu_kb(connected))
        await safe_answer(callback)
        return


    if action == "games":
        from keyboards.inline import games_kb
        text = "\n".join([
            "🎮 <b>Мини-игры</b>",
            "━━━━━━━━━━━━━━━━━━━━",
            "Нажми подсказку или введи команду:",
            "› <code>/rps</code> · <code>/guess</code> · <code>/hangman</code>",
            "› <code>/bj</code> · <code>/trivia</code> · <code>/статья 19</code>",
            "› <code>/minigames</code> — полный список",
        ])
        await safe_edit(callback.message, text, games_kb())
        await safe_answer(callback)
        return

    if action == "profile":
        conn = await get_connection(user.id)
        xp, level = (0, 1)
        rank_level = 0
        bal = 0
        if conn:
            xp, level = await _safe_xp(conn, user.id)
            rank_level = await get_user_rank(conn, user.id)
            bal = await get_balance(conn, user.id)
        if config.is_owner(user.id):
            rank_level = 7
        info = get_rank_info(rank_level)
        bar = progress_bar(xp % 100, 100)
        text = card(
            "Профиль",
            f"👤 <b>{html_esc(user.first_name or '')}</b>\n"
            f"ID: <code>{user.id}</code>\n"
            f"Username: @{html_esc(user.username or '—')}\n"
            f"{HR_LIGHT}\n"
            f"🏅 Ранг: {info.emoji} <b>{info.name}</b> [{rank_level}]\n"
            f"✨ Уровень: <b>{level}</b>\n"
            f"XP: {xp}  {bar}\n"
            f"💰 Баланс: <b>{bal}</b> монет\n"
            f"{HR_LIGHT}\n"
            f"Чат: <code>{conn or 'не привязан'}</code>",
            emoji="👤",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "ranks":
        text = card(
            "Система рангов",
            rank_list_text("ru")
            + f"\n{HR_LIGHT}\n"
            + "В группе: <code>/setrank</code> · <code>/myrank</code> · <code>/staff</code>",
            emoji="🏅",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "chats":
        conn = await get_connection(user.id)
        text = card(
            "Мои чаты",
            f"Привязанный чат: <code>{conn or 'нет'}</code>\n\n"
            f"Чтобы управлять группой из ЛС:\n"
            f"1. В группе напиши <code>/connect</code>\n"
            f"2. Здесь появится привязка\n"
            f"3. Команды модерации будут работать на этот чат",
            emoji="🔗",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "settings":
        prefs = await get_user_prefs(user.id)
        text = card(
            "Настройки",
            "Персональные предпочтения бота.\nНажми на пункт, чтобы переключить.",
            emoji="⚙️",
        )
        await safe_edit(callback.message, text, settings_kb(prefs))
        await safe_answer(callback)
        return

    if action.startswith("set:"):
        key = action.split(":", 1)[1]
        prefs = await get_user_prefs(user.id)
        if key == "lang":
            new = "en" if prefs.get("lang") == "ru" else "ru"
            await set_user_pref(user.id, "lang", new)
        elif key in ("notify_punish", "notify_levelup"):
            cur = prefs.get(key, 1)
            await set_user_pref(user.id, key, 0 if cur else 1)
        prefs = await get_user_prefs(user.id)
        text = card("Настройки", "Обновлено ✓", emoji="⚙️")
        await safe_edit(callback.message, text, settings_kb(prefs))
        await safe_answer(callback, "Сохранено")
        return

    if action == "stats":
        text = card(
            "Статистика",
            "Глобальная статистика доступна владельцу бота: <code>/botstats</code>\n"
            "В группе: <code>/stats</code> · <code>/toplevel</code> · <code>/reptop</code>",
            emoji="📊",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "eco":
        conn = await get_connection(user.id)
        if not conn:
            text = card(
                "Экономика",
                "Привяжи чат через <code>/connect</code> в группе,\n"
                "затем возвращайся сюда.\n\n"
                "В группе: <code>/daily</code> · <code>/balance</code> · <code>/pay</code> · <code>/topcoins</code>",
                emoji="💰",
            )
            await safe_edit(callback.message, text, back_main_kb())
            await safe_answer(callback)
            return
        bal = await get_balance(conn, user.id)
        text = card(
            "Экономика",
            f"💰 Баланс: <b>{bal}</b> монет\n"
            f"Чат: <code>{conn}</code>\n\n"
            f"Ежедневная награда: кнопка ниже или <code>/daily</code> в группе",
            emoji="💰",
        )
        b = InlineKeyboardBuilder()
        b.row(InlineKeyboardButton(text="🎁 Забрать daily", callback_data="cab:daily"))
        b.row(InlineKeyboardButton(text="‹  В главное меню", callback_data="cab:home"))
        await safe_edit(callback.message, text, b.as_markup())
        await safe_answer(callback)
        return

    if action == "daily":
        conn = await get_connection(user.id)
        if not conn:
            await safe_answer(callback, "Сначала /connect в группе", show_alert=True)
            return
        ok_claim, bal, streak = await claim_daily(conn, user.id)
        if ok_claim:
            await safe_answer(callback, f"+монеты! Баланс {bal}, серия {streak}", show_alert=True)
        else:
            await safe_answer(callback, "Уже получал сегодня", show_alert=True)
        return

    if action == "cmds":
        text = card(
            "Команды",
            f"В боте сотни команд.\n"
            f"Полный каталог: <code>/commands</code>\n"
            f"Справка по разделам: <code>/help</code>\n\n"
            f"Популярное:\n"
            f"· <code>/ban</code> <code>/mute</code> <code>/warn</code>\n"
            f"· <code>/lock</code> <code>/filters</code> <code>/notes</code>\n"
            f"· <code>/setrank</code> <code>/staff</code> <code>/settings</code>\n"
            f"· <code>/menu</code> — это меню",
            emoji="📚",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "help":
        text = card(
            "Справка",
            "1. Добавь бота в группу админом\n"
            "2. Выдай права на удаление и бан\n"
            "3. Настрой через <code>/settings</code>\n"
            "4. Назначь штат: <code>/setrank</code>\n"
            "5. В ЛС используй <code>/menu</code> для кабинета\n\n"
            "Подробнее: <code>/commands</code> · <code>/ranks</code>",
            emoji="❓",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "support":
        text = card(
            "Поддержка",
            "Напиши сюда свой вопрос — владелец бота увидит обращение.\n"
            "Или создай тикет в группе: <code>/ticket тема</code>",
            emoji="🎫",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "about":
        text = card(
            f"{config.BOT_NAME}",
            f"Версия: <code>{config.VERSION}</code>\n"
            f"Стек: Python · aiogram 3 · SQLite\n"
            f"Лицензия: MIT\n\n"
            f"Модерация · ранги · экономика · капча ·\n"
            f"федерации · XP · розыгрыши · заметки ·\n"
            f"40+ замков · антирейд · личный кабинет",
            footer="Сделано с вниманием к деталям",
            emoji="ℹ️",
        )
        await safe_edit(callback.message, text, back_main_kb())
        await safe_answer(callback)
        return

    if action == "disconnect":
        from database.db import disconnect_chat
        try:
            await disconnect_chat(user.id)
        except Exception:
            pass
        text, _ = await build_home_text(user, bot)
        await safe_edit(callback.message, text + "\n\n🔓 Чат отвязан", main_menu_kb(False))
        await safe_answer(callback, "Отвязано")
        return

    await safe_answer(callback)
