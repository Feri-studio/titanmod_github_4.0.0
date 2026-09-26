"""TitanMod visual system — единый стиль текстов (HTML)."""
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


def card(
    title: str,
    body: str = "",
    footer: str | None = None,
    emoji: str = "",
    accent: str | None = None,
) -> str:
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
    return f"❌ <b>Не получилось</b>\n{HR_LIGHT}\n{text}"


def warn(text: str) -> str:
    return f"⚠️ <b>Внимание</b>\n{HR_LIGHT}\n{text}"


def info(text: str) -> str:
    return f"ℹ️ <b>Информация</b>\n{HR_LIGHT}\n{text}"


def usage(command: str, examples: list[str], note: str | None = None) -> str:
    lines = [
        "📝 <b>Как пользоваться</b>",
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
        "❓ <b>Такой команды нет</b>",
        HR,
        f"Запрос: <code>/{c}</code>",
        "",
        "<b>Что можно сделать</b>",
        f"  {BULLET} Проверь написание",
        f"  {BULLET} Список: <code>/commands</code>",
        f"  {BULLET} Справка: <code>/help</code>",
        f"  {BULLET} Кабинет в ЛС: <code>/menu</code>",
        HR_LIGHT,
        "<i>TitanMod подскажет, если команда написана с ошибкой</i>",
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
    lines.extend([HR_LIGHT, "<i>Можно ответить на сообщение или указать id / @username</i>"])
    return "\n".join(lines)


def need_reply(command: str) -> str:
    return bad_args(
        command,
        "Нужен <b>ответ на сообщение</b> пользователя либо <code>id</code> / <code>@username</code>.",
        [f"/{command.lstrip('/')} 1h спам", f"/{command.lstrip('/')} @user"],
    )


def no_permission(what: str = "эту команду") -> str:
    return "\n".join([
        "🚫 <b>Недостаточно прав</b>",
        HR_LIGHT,
        f"Действие недоступно: <b>{html_esc(what)}</b>",
        "Нужны права админа Telegram или ранг штата бота.",
    ])


def progress_bar(value: int, maximum: int, length: int = 12) -> str:
    if maximum <= 0:
        return "░" * length
    filled = min(length, max(0, round(value / maximum * length)))
    return "█" * filled + "░" * (length - filled)


def rules_card(chat_title: str, rules_text: str) -> str:
    body = (rules_text or "").strip() or (
        f"<i>Правила ещё не заданы.</i>\n"
        f"{BULLET} Админ: <code>/setrules текст правил</code>"
    )
    return card(
        f"Правила · {html_esc(chat_title or 'чат')}",
        body,
        footer="Изменить: /setrules · личные: /privaterules",
        emoji="📜",
    )


def action_card(action: str, target, admin, reason: str, extra: str = "") -> str:
    from core.text import mention
    lines = [
        f"<b>{action}</b>",
        HR,
        f"👤 Участник — {mention(target)}",
        f"🛡 Модератор — {mention(admin)}",
        f"📄 Причина — {html_esc(reason or 'не указана')}",
    ]
    if extra:
        lines.append(f"⏱ {html_esc(extra)}")
    lines.extend([HR_LIGHT, "<i>TitanMod · модерация</i>"])
    return "\n".join(lines)


def rank_card(who: str, rank_title: str, level: int, extra: str = "") -> str:
    bar = progress_bar(level, 7, 7)
    lines = [
        "🏅 <b>Ранг в штате</b>",
        HR,
        f"👤 {who}",
        f"{BULLET} {rank_title}",
        f"{BULLET} Уровень <code>{level}</code>  {bar}",
    ]
    if extra:
        lines.append(extra)
    lines.extend([HR_LIGHT, "<i>/ranks · /stafflist · /setrank</i>"])
    return "\n".join(lines)


def cabinet_header(name: str, rank_title: str, xp: int = 0, level: int = 1) -> str:
    bar = progress_bar(int(xp) % 100, 100, 10)
    return "\n".join([
        "🏠 <b>Личный кабинет</b>",
        HR,
        f"Привет, <b>{html_esc(name)}</b>!",
        f"{BULLET} Ранг: {rank_title}",
        f"{BULLET} Опыт: <b>{xp}</b> · уровень <b>{level}</b>",
        f"{BULLET} {bar}",
        HR_LIGHT,
        "<i>Выбери раздел кнопкой ниже</i>",
    ])


def welcome_private(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return "\n".join([
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>",
        HR,
        f"Привет, <b>{html_esc(name)}</b>!",
        "",
        "Я помогаю с модерацией групп: баны, варны, ранги, экономика и автомод.",
        "",
        "<b>С чего начать</b>",
        f"  {BULLET} <code>/menu</code> — личный кабинет",
        f"  {BULLET} <code>/commands</code> — все команды",
        f"  {BULLET} <code>/help</code> — краткая справка",
        HR_LIGHT,
        "<i>Добавь меня в группу и выдай права администратора</i>",
    ])


def welcome_group(name: str, version: str, bot_name: str = "TitanMod") -> str:
    return "\n".join([
        f"✨ <b>{html_esc(bot_name)}</b>  <code>v{html_esc(version)}</code>",
        HR,
        f"Привет, <b>{html_esc(name)}</b>! Я на связи в этом чате.",
        "",
        "<b>Полезное админам</b>",
        f"  {BULLET} <code>/settings</code> — настройки чата",
        f"  {BULLET} <code>/commands</code> — каталог команд",
        f"  {BULLET} <code>/rules</code> · <code>/ranks</code>",
        f"  {BULLET} <code>/preset normal</code> — готовый автомод",
        HR_LIGHT,
        "🏠 В личке удобнее: <code>/menu</code>",
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
