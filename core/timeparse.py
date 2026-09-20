import re
from datetime import datetime, timedelta
from typing import Optional

_PATTERN = re.compile(
    r"^(?:(\d+)\s*(y|year|years|г|год|года|лет))?"
    r"(?:(\d+)\s*(w|week|weeks|н|нед|неделя|недель|недели))?"
    r"(?:(\d+)\s*(d|day|days|д|день|дня|дней))?"
    r"(?:(\d+)\s*(h|hour|hours|ч|час|часа|часов))?"
    r"(?:(\d+)\s*(m|min|mins|minute|minutes|м|мин|минута|минуты|минут))?"
    r"(?:(\d+)\s*(s|sec|secs|second|seconds|с|сек|секунда|секунды|секунд))?$",
    re.IGNORECASE,
)

_SIMPLE = re.compile(r"^(\d+)([smhdwуyгчмдсн])$", re.IGNORECASE)

_UNIT_SECONDS = {
    "s": 1, "с": 1, "sec": 1, "secs": 1, "second": 1, "seconds": 1,
    "секунда": 1, "секунды": 1, "секунд": 1, "сек": 1,
    "m": 60, "м": 60, "min": 60, "mins": 60, "minute": 60, "minutes": 60,
    "мин": 60, "минута": 60, "минуты": 60, "минут": 60,
    "h": 3600, "ч": 3600, "hour": 3600, "hours": 3600,
    "час": 3600, "часа": 3600, "часов": 3600,
    "d": 86400, "д": 86400, "day": 86400, "days": 86400,
    "день": 86400, "дня": 86400, "дней": 86400,
    "w": 604800, "н": 604800, "week": 604800, "weeks": 604800,
    "нед": 604800, "неделя": 604800, "недель": 604800, "недели": 604800,
    "y": 31536000, "г": 31536000, "у": 31536000, "year": 31536000, "years": 31536000,
    "год": 31536000, "года": 31536000, "лет": 31536000,
}


def parse_time(text: Optional[str], default: int = 3600) -> int:
    if not text:
        return default
    raw = text.strip().lower().replace(" ", "")
    m = _SIMPLE.match(raw)
    if m:
        value, unit = m.group(1), m.group(2)
        return int(value) * _UNIT_SECONDS.get(unit, default)
    compact = text.strip().lower().replace(" ", "")
    total = 0
    for mm in re.finditer(r"(\d+)([a-zа-яё]+)", compact, re.IGNORECASE):
        num = int(mm.group(1))
        unit = mm.group(2)
        if unit in _UNIT_SECONDS:
            total += num * _UNIT_SECONDS[unit]
        elif unit[:1] in _UNIT_SECONDS:
            total += num * _UNIT_SECONDS[unit[:1]]
    if total > 0:
        return total
    if text.strip().isdigit():
        return int(text.strip()) * 60
    return default


def parse_timedelta(text: Optional[str], default: int = 3600) -> timedelta:
    return timedelta(seconds=parse_time(text, default))


def format_time(seconds: int) -> str:
    if seconds is None or seconds <= 0:
        return "навсегда"
    seconds = int(seconds)
    parts = []
    years, seconds = divmod(seconds, 31536000)
    days, seconds = divmod(seconds, 86400)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    if years:
        parts.append(f"{years} г.")
    if days:
        parts.append(f"{days} д.")
    if hours:
        parts.append(f"{hours} ч.")
    if minutes:
        parts.append(f"{minutes} мин.")
    if seconds and not parts:
        parts.append(f"{seconds} сек.")
    return " ".join(parts) or "0 сек."


def until_from_now(seconds: int) -> datetime:
    return datetime.utcnow() + timedelta(seconds=max(0, int(seconds)))


def parse_hhmm(text: str) -> Optional[tuple[int, int]]:
    m = re.match(r"^(\d{1,2}):(\d{2})$", (text or "").strip())
    if not m:
        return None
    h, mi = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mi <= 59:
        return h, mi
    return None


def is_night(now: datetime, start: str, end: str) -> bool:
    s = parse_hhmm(start)
    e = parse_hhmm(end)
    if not s or not e:
        return False
    cur = now.hour * 60 + now.minute
    a = s[0] * 60 + s[1]
    b = e[0] * 60 + e[1]
    if a == b:
        return False
    if a < b:
        return a <= cur < b
    return cur >= a or cur < b
