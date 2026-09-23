"""TitanMod visual system — rich Telegram HTML cards."""
from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest

from core.text import html_esc

HR = "━━━━━━━━━━━━━━━━━━━━"
HR_LIGHT = "────────────────────"
BULLET = "›"

CAT_EMOJI = {
    "punish": "🔨", "warns": "⚠️", "locks": "🔒", "welcome": "👋",
    "notes": "📝", "filters": "🔎", "fed": "🕸", "sec": "🛡",
    "admin": "⚙️", "info": "ℹ️", "util": "🧰", "fun": "🎮",
    "owner": "👑", "ranks": "🏅", "economy": "💰", "tickets": "🎫",
    "cabinet": "🏠", "xp": "✨", "giveaway": "🎁",
}


def card(title: str, body: str = "", footer: str | None = None, emoji: str = "", accent: str | None = None) -> str:
    em = f"{emoji} " if emoji else ""
    parts = [f"{em}<b>{title}</b>", accent or HR]
    if body:
        parts.append(body.strip())
    if footer:
        parts.extend([HR_LIGHT, f"<i>{footer}</i>"])
    return "\n".join(parts)


def panel(title: str, rows: list[tuple[str, str]], emoji: str = "✦") -> str:
    lines = [f"{emoji} <b>{title}</b>", HR]
    for k, v in rows:
        lines.append(f"{BULLET} <b>{k}</b> — {v}")
    return "\n".join(lines)


def section(title: str, lines: list[str] | str, emoji: str = "") -> str:
    head = f"{emoji} <b>{title}</b>" if emoji else f"<b>{title}</b>"
    body = lines if isinstance(lines, str) else "\n".join(f"{BULLET} {x}" for x in lines)
    return f"{head}\n{body}"


def kv(rows: list[tuple[str, object]], sep: str = " — ") -> str:
    return "\n".join(f"{BULLET} <b>{key}</b>{sep}{val}" for key, val in rows)


def ok(text: str) -> str:
    return f"✅ <b>Готово</b>\n{HR_LIGHT}\n{text}"


def fail(text: str) -> str:
    return f"❌ <b>Ошибка</b>\n{HR_LIGHT}\n{text}"


def warn(text: str) -> str:
    return f"⚠️ <b>Внимание</b>\n{HR_LIGHT}\n{text}"


def info(text: str) -> str:
    return f"ℹ️ <b>Инфо</b>\n{HR_LIGHT}\n{text}"


def usage(command: str, examples: list[str], note: str | None = None) -> str:
    lines = [
        "📝 <b>Как использовать</b>",
        HR,
        f"Команда: <code>/{html_esc(command.lstrip('/'))}</code>",
        "",
        "<b>Примеры</b>",
    ]
    for ex in examples:
        lines.append(f"  {BULLET} <code>{html_esc(ex)}</code>")
    if note:
        lines.extend([HR_LIGHT, f"<i>{note}</i>"])
    return "\n".join(lines)


def unknown_command(cmd: str) -> str:
    c = html_esc((cmd or "").lstrip("/")[:40])
    return "\n".join([
        "❓ <b>Команда не найдена</b>",
        HR,
        f"Неизвестно: <code>/{c}</code>",
        "",
        "<b>Что сделать</b>",
        f"  {BULLET} Проверь написание",
        f"  {BULLET} <code>/commands</code> — каталог",
        f"  {BULLET} <code>/help</code> — справка",
        f"  {BULLET} <code>/menu</code> — кабинет в ЛС",
        HR_LIGHT,
        "<i>TitanMod</i>",
    ])


def bad_args(command: str, hint: str, examples: list[str] | None = None) -> str:
    lines = [
        "✍️ <b>Неверный формат</b>",
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
    lines.extend([HR_LIGHT, "<i>Reply на сообщение или id / @username</i>"])
    return "\n".join(lines)


def need_reply(command: str) -> str:
    return bad_args(
        command,
        "Нужен <b>ответ</b> на сообщение или <code>id</code> / <code>@user</code>.",
        [f"/{command.lstrip('/')} 1h спам", f"/{command.lstrip('/')} @user"],
    )


def no_permission(what: str = "эту команду") -> str:
    return "\n".join([
        "🚫 <b>Нет доступа</b>",
        HR_LIGHT,
        f"Недостаточно прав: <b>{html_esc(what)}</b>",
        "Нужен админ Telegram или ранг штата бота.",
    ])


def progress_bar(value: int, maximum: int, length: int = 12) -> str:
    if maximum <= 0:
        return "░" * length
    filled = min(length, max(0, round(value / maximum * length)))
    return "█" * filled + "░" * (length - filled)


def rules_card(chat_title: str, rules_text: str) -> str:
    body = (rules_text or "").strip() or (
        f"<i>Правила ещё не заданы.</i>\n{BULLET} <code>/setrules текст</code>"
    )
    return card(
        f"Правила · {html_esc(chat_title or 'чат')}",
        body,
        footer="TitanMod · /setrules · /privaterules",
        emoji="📜",
    )


def action_card(action: str, target, admin, reason: str, extra: str = "") -> str:
    from core.text import mention
    lines = [
        f"<b>{action}</b>",
        HR,
        f"👤 Цель — {mention(target)}",
        f"🛡 Модер — {mention(admin)}",
        f"📄 Причина — {html_esc(reason or '—')}",
    ]
    if extra:
        lines.append(f"⏱ {html_esc(extra)}")
    lines.extend([HR_LIGHT, "<i>TitanMod moderation</i>"])
    return "\n".join(lines)


def rank_card(who: str, rank_title: str, level: int, extra: str = "") -> str:
    bar = progress_bar(level, 7, 7)
    lines = [
        "🏅 <b>Ранг</b>",
        HR,
        f"👤 {who}",
        f"{BULLET} {rank_title}",
        f"{BULLET} Уровень <code>{level}</code>  {bar}",
    ]
    if extra:
        lines.append(extra)
    lines.extend([HR_LIGHT, "<i>/ranks · /stafflist</i>"])
    return "\n".join(lines)


def cabinet_header(name: str, rank_title: str, xp: int = 0, level: int = 1) -> str:
    bar = progress_bar(int(xp) % 100, 100, 10)
    return "\n".join([
        "🏠 <b>Личный кабинет</b>",
        HR,
        f"Привет, <b>{name}</b>!",
        f"{BULLET} Ранг: {rank_title}",
        f"{BULLET} XP: <b>{xp}</b> · lvl <b>{level}</b>",
        f"{BULLET} {bar}",
        HR_LIGHT,
        "<i>Выбери раздел ниже</i>",
    ])


def welcome_private(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return "\n".join([
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>",
        HR,
        f"Привет, <b>{html_esc(name)}</b>!",
        "",
        "Модерация · ранги · экономика · тикеты",
        "",
        "<b>Старт</b>",
        f"  {BULLET} <code>/menu</code> — кабинет",
        f"  {BULLET} <code>/commands</code> — каталог",
        f"  {BULLET} <code>/help</code> — справка",
        HR_LIGHT,
        "<i>Добавь бота в группу как админа</i>",
    ])


def welcome_group(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return "\n".join([
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>",
        HR,
        f"Привет, <b>{html_esc(name)}</b>!",
        "",
        f"{BULLET} <code>/settings</code> · <code>/commands</code>",
        f"{BULLET} <code>/ranks</code> · <code>/rules</code>",
        f"{BULLET} <code>/preset normal</code>",
        HR_LIGHT,
        "🏠 ЛС: <code>/menu</code>",
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
