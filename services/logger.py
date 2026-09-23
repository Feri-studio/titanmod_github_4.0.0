from aiogram import Bot
from database.db import get_settings, add_event


async def send_log(bot: Bot, chat_id: int, event: str, text: str, user_id=None, admin_id=None):
    """Write event_log and optionally forward to log_chat_id."""
    event = (event or "event").lower().strip()
    try:
        await add_event(chat_id, event, user_id, admin_id, text)
    except Exception:
        pass
    try:
        settings = await get_settings(chat_id)
    except Exception:
        return
    raw = settings.get("log_events") or ""
    events = [e.strip().lower() for e in raw.split(",") if e.strip()]
    # if list configured and event not in it — skip telegram send (still in DB)
    if events and event not in events:
        return
    dest = settings.get("log_chat_id")
    if not dest:
        return
    try:
        await bot.send_message(int(dest), text, disable_web_page_preview=True)
    except Exception:
        pass
