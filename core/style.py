"""Pretty HTML cards for Telegram messages."""
from __future__ import annotations

from aiogram.exceptions import TelegramBadRequest

from core.text import html_esc

HR = "──────────────"
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
}


def card(title: str, body: str = "", footer: str | None = None) -> str:
    parts = [f"<b>{title}</b>", HR]
    if body:
        parts.append(body.strip())
    if footer:
        parts.append(HR)
        parts.append(f"<i>{footer}</i>")
    return "\n".join(parts)


def kv(rows: list[tuple[str, object]]) -> str:
    lines = []
    for key, val in rows:
        lines.append(f"{key}: {val}")
    return "\n".join(lines)


def ok(text: str) -> str:
    return f"✅ {text}"


def fail(text: str) -> str:
    return f"❌ {text}"


def warn(text: str) -> str:
    return f"⚠️ {text}"


def action_card(action: str, target, admin, reason: str, extra: str = "") -> str:
    from core.text import mention

    lines = [
        f"<b>{action}</b>",
        HR,
        f"👤 {mention(target)}",
        f"🛡 {mention(admin)}",
        f"📌 {html_esc(reason or 'без причины')}",
    ]
    if extra:
        lines.append(f"⏱ {html_esc(extra)}")
    return "\n".join(lines)


async def safe_edit(message, text: str, reply_markup=None):
    try:
        await message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=True)
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return
        try:
            await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=True)
        except Exception:
            pass
    except Exception:
        pass
