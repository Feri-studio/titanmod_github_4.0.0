import re
from aiogram.types import Message, User


async def extract_target(message: Message, args: str = "") -> tuple[User | None, str]:
    """Return (user, leftover_args). Prefer reply, then mention/id in args."""
    leftover = args or ""
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, leftover.strip()

    if message.entities:
        for ent in message.entities:
            if ent.type == "text_mention" and ent.user:
                return ent.user, leftover.strip()

    if leftover:
        parts = leftover.split(maxsplit=1)
        token = parts[0]
        rest = parts[1] if len(parts) > 1 else ""
        if token.startswith("@"):
            return None, leftover
        if token.isdigit() or (token.startswith("-") and token[1:].isdigit()):
            user = User(id=int(token), is_bot=False, first_name=str(token))
            return user, rest
        m = re.match(r"^https://t\.me/(.+)$", token)
        if m:
            return None, leftover
    return None, leftover.strip()


def extract_reason(args: str, default: str = "Без причины") -> tuple[str | None, str]:
    """Parse optional time as first token then reason."""
    if not args:
        return None, default
    parts = args.split(maxsplit=1)
    first = parts[0]
    rest = parts[1] if len(parts) > 1 else default
    if re.match(r"^\d+[smhdwуyгчмдсн]$", first, re.I) or re.match(r"^(\d+[a-zа-яё]+)+$", first, re.I):
        return first, rest if rest else default
    return None, args
