import html
import re
from datetime import datetime
from typing import Any, Optional


def html_esc(text: Any) -> str:
    return html.escape("" if text is None else str(text), quote=False)


def code(text: Any) -> str:
    return f"<code>{html_esc(text)}</code>"


def mention(user) -> str:
    if user is None:
        return "Unknown"
    name = html_esc(getattr(user, "full_name", None) or getattr(user, "first_name", None) or "User")
    uid = getattr(user, "id", 0)
    return f'<a href="tg://user?id={uid}">{name}</a>'


def user_title(user) -> str:
    if user is None:
        return "Unknown"
    name = getattr(user, "full_name", None) or "User"
    uname = getattr(user, "username", None)
    uid = getattr(user, "id", 0)
    extra = f" @{uname}" if uname else ""
    return f"{name}{extra} [{uid}]"


def shorten(text: str, limit: int = 400) -> str:
    text = text or ""
    if len(text) <= limit:
        return text
    return text[: limit - 1] + "…"


def fill_welcome(template: str, user, chat, count: int = 0, rules: str = "") -> str:
    first = html_esc(getattr(user, "first_name", "") or "")
    last = html_esc(getattr(user, "last_name", "") or "")
    name = html_esc(getattr(user, "full_name", None) or first or "друг")
    uname = f"@{user.username}" if getattr(user, "username", None) else name
    chat_title = html_esc(getattr(chat, "title", None) or "чат")
    data = {
        "{user}": mention(user),
        "{mention}": mention(user),
        "{name}": name,
        "{first}": first,
        "{last}": last,
        "{chat}": chat_title,
        "{id}": str(getattr(user, "id", "")),
        "{username}": html_esc(uname),
        "{count}": str(count or ""),
        "{date}": datetime.utcnow().strftime("%d.%m.%Y"),
        "{rules}": rules or "правила",
    }
    text = template or ""
    for k, v in data.items():
        text = text.replace(k, v)
    return text


_RTL_RE = re.compile(r"[\u0590-\u08FF\uFB1D-\uFEFC]")
_ZALGO_RE = re.compile(r"[\u0300-\u036f\u0489-\u0489\u1ab0-\u1aff\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]")
_CYR_RE = re.compile(r"[А-Яа-яЁё]")
_LAT_RE = re.compile(r"[A-Za-z]")
_ARABIC_RE = re.compile(r"[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]")
_CJK_RE = re.compile(r"[\u4E00-\u9FFF\u3400-\u4DBF\u3040-\u30FF]")
_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001F5FF"
    "\U0001F600-\U0001F64F"
    "\U0001F680-\U0001F6FF"
    "\U0001F700-\U0001F77F"
    "\U0001F780-\U0001F7FF"
    "\U0001F800-\U0001F8FF"
    "\U0001F900-\U0001F9FF"
    "\U0001FA00-\U0001FAFF"
    "\U00002702-\U000027B0"
    "\U0000FE0F"
    "]+",
    flags=re.UNICODE,
)
_URL_RE = re.compile(
    r"(https?://\S+|www\.\S+|t\.me/\S+|telegram\.me/\S+|tg://\S+)",
    re.IGNORECASE,
)
_INVITE_RE = re.compile(r"(t\.me/\+|telegram\.me/\+|joinchat/|t\.me/joinchat/)", re.IGNORECASE)
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+?\d[\d\-\s\(\)]{8,}\d)")
_HASHTAG_RE = re.compile(r"(^|\s)#[\w]{2,}", re.UNICODE)
_CASHTAG_RE = re.compile(r"(^|\s)\$[A-Z]{2,6}\b")
_MENTION_RE = re.compile(r"@\w{3,}")


def has_rtl(text: str) -> bool:
    return bool(_RTL_RE.search(text or ""))


def zalgo_count(text: str) -> int:
    return len(_ZALGO_RE.findall(text or ""))


def has_cyrillic(text: str) -> bool:
    return bool(_CYR_RE.search(text or ""))


def has_latin(text: str) -> bool:
    return bool(_LAT_RE.search(text or ""))


def has_arabic(text: str) -> bool:
    return bool(_ARABIC_RE.search(text or ""))


def has_cjk(text: str) -> bool:
    return bool(_CJK_RE.search(text or ""))


def emoji_count(text: str) -> int:
    return len(_EMOJI_RE.findall(text or ""))


def extract_urls(text: str) -> list[str]:
    return _URL_RE.findall(text or "")


def has_invite(text: str) -> bool:
    return bool(_INVITE_RE.search(text or ""))


def has_email(text: str) -> bool:
    return bool(_EMAIL_RE.search(text or ""))


def has_phone(text: str) -> bool:
    return bool(_PHONE_RE.search(text or ""))


def has_hashtag(text: str) -> bool:
    return bool(_HASHTAG_RE.search(text or ""))


def has_cashtag(text: str) -> bool:
    return bool(_CASHTAG_RE.search(text or ""))


def mention_count(text: str) -> int:
    return len(_MENTION_RE.findall(text or ""))


def caps_ratio(text: str) -> float:
    letters = [c for c in (text or "") if c.isalpha()]
    if not letters:
        return 0.0
    upper = sum(1 for c in letters if c.isupper())
    return upper / len(letters) * 100.0


def looks_like_url_name(name: str) -> bool:
    return bool(_URL_RE.search(name or "")) or "t.me/" in (name or "").lower()
