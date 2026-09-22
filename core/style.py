"""TitanMod visual system — polished HTML cards, errors, usage hints."""
from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest

from core.text import html_esc

# ── Borders & accents ─────────────────────────────────────────────
HR = "━━━━━━━━━━━━━━━━━━━━"
HR_LIGHT = "────────────────────"
HR_DOT = "· · · · · · · · · · · ·"
BULLET = "›"
CHECK = "✓"
CROSS = "✕"

CAT_EMOJI = {
    "punish": "🔨",
    "warns": "⚠️",
    "locks": "🔒",
    "welcome": "👋",
    "notes": "📝",
    "filters": "🔎",
    "fed": "🕸",
    "sec": "🛡",
    "admin": "⚙️",
    "info": "ℹ️",
    "util": "🧰",
    "fun": "🎮",
    "owner": "👑",
    "ranks": "🏅",
    "economy": "💰",
    "tickets": "🎫",
    "cabinet": "🏠",
    "xp": "✨",
    "giveaway": "🎁",
}


def card(
    title: str,
    body: str = "",
    footer: str | None = None,
    emoji: str = "",
    accent: str | None = None,
) -> str:
    """Main message card."""
    em = f"{emoji} " if emoji else ""
    bar = accent or HR
    parts = [f"{em}<b>{title}</b>", bar]
    if body:
        parts.append(body.strip())
    if footer:
        parts.append(HR_LIGHT)
        parts.append(f"<i>{footer}</i>")
    return "\n".join(parts)


def panel(title: str, rows: list[tuple[str, str]], emoji: str = "✦") -> str:
    """Key-value panel."""
    lines = [f"{emoji} <b>{title}</b>", HR]
    for k, v in rows:
        lines.append(f"<b>{k}</b>  ·  {v}")
    return "\n".join(lines)


def section(title: str, lines: list[str] | str, emoji: str = "") -> str:
    head = f"{emoji} <b>{title}</b>" if emoji else f"<b>{title}</b>"
    body = lines if isinstance(lines, str) else "\n".join(f"{BULLET} {x}" for x in lines)
    return f"{head}\n{body}"


def kv(rows: list[tuple[str, object]], sep: str = "  ·  ") -> str:
    return "\n".join(f"<b>{key}</b>{sep}{val}" for key, val in rows)


def ok(text: str) -> str:
    return (
        f"✅ <b>Готово</b>\n"
        f"{HR_LIGHT}\n"
        f"{text}"
    )


def fail(text: str) -> str:
    return (
        f"❌ <b>Ошибка</b>\n"
        f"{HR_LIGHT}\n"
        f"{text}"
    )


def warn(text: str) -> str:
    return (
        f"⚠️ <b>Внимание</b>\n"
        f"{HR_LIGHT}\n"
        f"{text}"
    )


def info(text: str) -> str:
    return (
        f"ℹ️ <b>Инфо</b>\n"
        f"{HR_LIGHT}\n"
        f"{text}"
    )


def usage(command: str, examples: list[str], note: str | None = None) -> str:
    """Pretty usage / how-to for a command."""
    lines = [
        f"📝 <b>Как использовать</b>",
        HR,
        f"Команда: <code>/{html_esc(command.lstrip('/'))}</code>",
        "",
        "<b>Примеры</b>",
    ]
    for ex in examples:
        lines.append(f"  {BULLET} <code>{html_esc(ex)}</code>")
    if note:
        lines.append(HR_LIGHT)
        lines.append(f"<i>{note}</i>")
    return "\n".join(lines)


def unknown_command(cmd: str) -> str:
    c = html_esc((cmd or "").lstrip("/")[:40])
    return (
        f"❓ <b>Команда не найдена</b>\n"
        f"{HR}\n"
        f"Неизвестная команда: <code>/{c}</code>\n\n"
        f"<b>Что сделать</b>\n"
        f"  {BULLET} Проверь написание\n"
        f"  {BULLET} Список: <code>/commands</code>\n"
        f"  {BULLET} Справка: <code>/help</code>\n"
        f"  {BULLET} Меню в ЛС: <code>/menu</code>\n"
        f"{HR_LIGHT}\n"
        f"<i>TitanMod · подсказка при опечатке</i>"
    )


def bad_args(command: str, hint: str, examples: list[str] | None = None) -> str:
    """Wrong / missing arguments."""
    lines = [
        f"✍️ <b>Неверный формат</b>",
        HR,
        f"Команда: <code>/{html_esc(command.lstrip('/'))}</code>",
        "",
        hint.strip(),
    ]
    if examples:
        lines.append("")
        lines.append("<b>Примеры</b>")
        for ex in examples:
            lines.append(f"  {BULLET} <code>{html_esc(ex)}</code>")
    lines.append(HR_LIGHT)
    lines.append("<i>Ответь на сообщение пользователя или укажи id / @username</i>")
    return "\n".join(lines)


def no_permission(what: str = "эту команду") -> str:
    return (
        f"🚫 <b>Нет доступа</b>\n"
        f"{HR_LIGHT}\n"
        f"Недостаточно прав для: <b>{html_esc(what)}</b>\n"
        f"Нужен статус админа Telegram или ранг штата бота."
    )


def need_reply(command: str) -> str:
    return bad_args(
        command,
        "Нужно <b>ответить</b> на сообщение пользователя\nили указать <code>id</code> / <code>@username</code>.",
        examples=[f"/{command.lstrip('/')} 1h спам", f"/{command.lstrip('/')} @user причина"],
    )


def progress_bar(value: int, maximum: int, length: int = 12) -> str:
    if maximum <= 0:
        return "░" * length
    filled = min(length, max(0, round(value / maximum * length)))
    return "█" * filled + "░" * (length - filled)


def rules_card(chat_title: str, rules_text: str) -> str:
    body = (rules_text or "").strip() or (
        f"<i>Правила ещё не заданы.</i>\n"
        f"{BULLET} Админ: <code>/setrules текст</code>"
    )
    return card(
        f"Правила · {html_esc(chat_title or 'чат')}",
        body,
        footer="TitanMod · /setrules · /privaterules · /clearrules",
        emoji="📜",
    )


def action_card(action: str, target, admin, reason: str, extra: str = "") -> str:
    from core.text import mention

    lines = [
        f"<b>{action}</b>",
        HR,
        f"👤 Цель     · {mention(target)}",
        f"🛡 Модер    · {mention(admin)}",
        f"📄 Причина · {html_esc(reason or '—')}",
    ]
    if extra:
        lines.append(f"⏱ {html_esc(extra)}")
    lines.append(HR_LIGHT)
    lines.append("<i>TitanMod moderation</i>")
    return "\n".join(lines)


def welcome_private(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return (
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>\n"
        f"{HR}\n"
        f"Привет, <b>{html_esc(name)}</b>!\n\n"
        f"Мощный бот модерации: ранги, экономика, тикеты, автомод.\n\n"
        f"<b>Быстрый старт</b>\n"
        f"  {BULLET} <code>/menu</code> — личный кабинет\n"
        f"  {BULLET} <code>/commands</code> — каталог команд\n"
        f"  {BULLET} <code>/help</code> — справка по разделам\n"
        f"  {BULLET} Добавь бота в группу → сделай админом\n"
        f"{HR_LIGHT}\n"
        f"<i>Группа: /settings · /ranks · /rules</i>"
    )


def welcome_group(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return (
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>\n"
        f"{HR}\n"
        f"Привет, <b>{html_esc(name)}</b>! Я в этом чате.\n\n"
        f"<b>Админам</b>\n"
        f"  {BULLET} <code>/settings</code> — настройки\n"
        f"  {BULLET} <code>/commands</code> — все команды\n"
        f"  {BULLET} <code>/ranks</code> — штат и иерархия\n"
        f"  {BULLET} <code>/rules</code> — правила\n"
        f"  {BULLET} <code>/preset normal</code> — автомод\n"
        f"{HR_LIGHT}\n"
        f"🏠 Личный кабинет в ЛС: <code>/menu</code>"
    )




def rank_card(who: str, rank_title: str, level: int, extra: str = "") -> str:
    bar = progress_bar(level, 7, 7)
    lines = [
        "🏅 <b>Ранг обновлён</b>",
        HR,
        f"👤 {who}",
        f"› {rank_title}",
        f"› Уровень <code>{level}</code>  {bar}",
    ]
    if extra:
        lines.append(extra)
    lines.append(HR_LIGHT)
    lines.append("<i>Иерархия TitanMod · /ranks · /stafflist</i>")
    return chr(10).join(lines)


def cabinet_header(name: str, rank_title: str, xp: int = 0, level: int = 1) -> str:
    bar = progress_bar(int(xp) % 100, 100, 10)
    return chr(10).join([
        "🏠 <b>Личный кабинет</b>",
        HR,
        f"Привет, <b>{name}</b>!",
        f"› Ранг: {rank_title}",
        f"› XP: <b>{xp}</b> · lvl <b>{level}</b>",
        f"› {bar}",
        HR_LIGHT,
        "<i>Выбери раздел ниже</i>",
    ])


async def safe_edit(message, text: str, reply_markup=None) -> None:
    try:
        await message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    except TelegramBadRequest:
        pass
    except Exception:
        pass


async def safe_answer(callback, text: str | None = None, show_alert: bool = False) -> None:
    try:
        await callback.answer(text, show_alert=show_alert)
    except Exception:
        pass
