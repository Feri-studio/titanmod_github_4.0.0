from aiogram.types import Message


def extract_media(message: Message) -> tuple[str | None, str | None]:
    src = message.reply_to_message or message
    if src.photo:
        return src.photo[-1].file_id, "photo"
    if src.video:
        return src.video.file_id, "video"
    if src.document:
        return src.document.file_id, "document"
    if src.animation:
        return src.animation.file_id, "animation"
    if src.audio:
        return src.audio.file_id, "audio"
    if src.voice:
        return src.voice.file_id, "voice"
    if src.sticker:
        return src.sticker.file_id, "sticker"
    if src.video_note:
        return src.video_note.file_id, "video_note"
    return None, None


async def send_saved(bot, chat_id, content, file_id=None, file_type=None, reply_markup=None, reply_to=None):
    kwargs = {"reply_markup": reply_markup, "reply_to_message_id": reply_to}
    kwargs = {k: v for k, v in kwargs.items() if v is not None}
    if file_id and file_type == "photo":
        return await bot.send_photo(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "video":
        return await bot.send_video(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "document":
        return await bot.send_document(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "animation":
        return await bot.send_animation(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "audio":
        return await bot.send_audio(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "voice":
        return await bot.send_voice(chat_id, file_id, caption=content, **kwargs)
    if file_id and file_type == "sticker":
        return await bot.send_sticker(chat_id, file_id, **kwargs)
    if file_id and file_type == "video_note":
        return await bot.send_video_note(chat_id, file_id, **kwargs)
    return await bot.send_message(chat_id, content or "…", **kwargs)
