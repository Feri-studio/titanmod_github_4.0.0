from aiogram.types import Message
from aiogram.enums import ContentType
from core.defaults import LOCK_TYPES
from core.text import (
    extract_urls, has_invite, has_email, has_phone, has_hashtag, has_cashtag,
    has_rtl, zalgo_count, has_cyrillic, has_latin, has_arabic, has_cjk,
    emoji_count, mention_count, caps_ratio,
)


def parse_lock_set(raw: str | None) -> set[str]:
    if not raw:
        return set()
    return {x.strip() for x in str(raw).split(",") if x.strip() in LOCK_TYPES}


def dump_lock_set(locks: set[str]) -> str:
    return ",".join(sorted(locks))


def content_locked(message: Message, locks: set[str], settings: dict) -> str | None:
    """Return lock key if message should be deleted."""
    if not locks:
        locks = set()
    text = message.text or message.caption or ""
    ctype = message.content_type

    if "all" in locks and ctype != ContentType.TEXT:
        return "all"
    if "all" in locks and text and not text.startswith("/"):
        return "all"

    mapping = {
        "photo": ctype == ContentType.PHOTO,
        "video": ctype == ContentType.VIDEO,
        "audio": ctype == ContentType.AUDIO,
        "voice": ctype == ContentType.VOICE,
        "video_note": ctype == ContentType.VIDEO_NOTE,
        "document": ctype == ContentType.DOCUMENT,
        "sticker": ctype == ContentType.STICKER,
        "gif": ctype == ContentType.ANIMATION,
        "poll": ctype == ContentType.POLL,
        "location": ctype in (ContentType.LOCATION, ContentType.VENUE),
        "contact": ctype == ContentType.CONTACT,
        "dice": ctype == ContentType.DICE,
        "invoice": ctype == ContentType.INVOICE,
        "game": ctype == ContentType.GAME,
        "games": ctype == ContentType.GAME,
    }
    if "media" in locks and ctype in {
        ContentType.PHOTO, ContentType.VIDEO, ContentType.AUDIO, ContentType.VOICE,
        ContentType.VIDEO_NOTE, ContentType.DOCUMENT, ContentType.ANIMATION, ContentType.STICKER,
    }:
        return "media"

    for key, hit in mapping.items():
        if hit and key in locks:
            return key

    if "forwards" in locks and (message.forward_date or message.forward_from or message.forward_from_chat):
        return "forwards"
    if "forwards_channel" in locks and message.forward_from_chat and message.forward_from_chat.type == "channel":
        return "forwards_channel"
    if "channel" in locks and getattr(message, "sender_chat", None) and message.sender_chat.id != message.chat.id:
        return "channel"
    if "via" in locks and getattr(message, "via_bot", None):
        return "via"
    if "inline" in locks and getattr(message, "via_bot", None):
        return "inline"
    if "button" in locks and message.reply_markup:
        return "button"
    if "caption" in locks and message.caption:
        return "caption"
    if "spoiler" in locks and message.has_media_spoiler:
        return "spoiler"
    if "premium" in locks and getattr(message, "premium_animation", None):
        return "premium"
    if "custom_emoji" in locks and message.entities:
        if any(e.type == "custom_emoji" for e in message.entities):
            return "custom_emoji"
    if "quote" in locks and getattr(message, "quote", None):
        return "quote"

    if text:
        if "url" in locks and extract_urls(text):
            return "url"
        if "invite" in locks and has_invite(text):
            return "invite"
        if "tg" in locks and ("t.me/" in text.lower() or "telegram.me/" in text.lower()):
            return "tg"
        if "email" in locks and has_email(text):
            return "email"
        if "phone" in locks and has_phone(text):
            return "phone"
        if "hashtag" in locks and has_hashtag(text):
            return "hashtag"
        if "cashtag" in locks and has_cashtag(text):
            return "cashtag"
        if "mention" in locks and mention_count(text) > 0:
            return "mention"
        if "rtl" in locks and has_rtl(text):
            return "rtl"
        if "zalgo" in locks and zalgo_count(text) >= int(settings.get("zalgo_limit", 8) or 8):
            return "zalgo"
        if "cyrillic" in locks and has_cyrillic(text):
            return "cyrillic"
        if "latin" in locks and has_latin(text):
            return "latin"
        if "arabic" in locks and has_arabic(text):
            return "arabic"
        if "chinese" in locks and has_cjk(text):
            return "chinese"
        if "emoji" in locks and emoji_count(text) > 0:
            return "emoji"
        if "command" in locks and text.startswith("/") and not _is_our(text):
            return "command"
        if "entities" in locks and (message.entities or message.caption_entities):
            return "entities"

    cap = int(settings.get("caps_percent", 80) or 80)
    minl = int(settings.get("caps_min", 12) or 12)
    if text and len(text) >= minl and caps_ratio(text) >= cap and "messages" in locks:
        return "messages"

    mention_limit = int(settings.get("mention_limit", 5) or 5)
    if mention_count(text) > mention_limit:
        return "mention"

    emoji_limit = int(settings.get("emoji_limit", 15) or 15)
    if emoji_count(text) > emoji_limit:
        return "emoji"

    return None


def _is_our(text: str) -> bool:
    cmd = text[1:].split()[0].split("@")[0].lower()
    return cmd in OUR_COMMANDS


OUR_COMMANDS = set()
