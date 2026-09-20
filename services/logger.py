from aiogram import Bot
from database.db import get_settings, add_event


async def send_log(bot: Bot, chat_id: int, event: str, text: str, user_id=None, admin_id=None):
    settings = await get_settings(chat_id)
    events = (settings.get("log_events") or "").split(",")
    events = [e.strip() for e in events if e.strip()]
    await add_event(chat_id, event, user_id, admin_id, text)
    if event not in events and events:
        return
    dest = settings.get("log_chat_id")
    if not dest:
        return
    try:
        await bot.send_message(int(dest), text, disable_web_page_preview=True)
    except Exception:
        pass
