"""TitanMod entrypoint — quality build 4.5."""
from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from database.db import init_db
from middlewares.context import ContextMiddleware
from middlewares.throttling import AntiFloodMiddleware
from middlewares.disable import DisableCommandMiddleware
from middlewares.aliases import AliasMiddleware
from middlewares.snipe_track import SnipeTrackMiddleware
from middlewares.activation import GroupActivationMiddleware
from middlewares.anticheat_mw import AntiCheatMiddleware
from services.scheduler import scheduler_loop
from services.locks import OUR_COMMANDS
from core.commands import ALL_COMMAND_NAMES
from handlers import security_ac, stats_ui, minigames, extra_pack, new_cmds
from handlers import (
    start, punish, warns, locks, welcome, notes, filters_cmd, federation,
    security, admin_tools, settings, info, extras, fun, owner, more, moderation,
    levels, giveaway, topics, quarantine, aliases, mass, backup, watch, catalog,
    ranks, cabinet, economy, synonyms, tickets, v42_tools, full_cmds, v45, activate,
)
from handlers.pack import utils_pack as pack_utils
from handlers.pack import fun_pack as pack_fun
from handlers.pack import reports_pack as pack_reports
from handlers.pack import economy_pack as pack_economy

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("titanmod")
OUR_COMMANDS.update(ALL_COMMAND_NAMES)


async def _warn_if_bot_lacks_rights(bot: Bot) -> None:
    """Log a clear hint when bot cannot restrict members in known chats."""
    try:
        from database.db import list_chats
        from core.permissions import admin_cache

        me = await bot.get_me()
        chats = await list_chats()
        checked = 0
        for row in chats[:30]:
            cid = row.get("chat_id")
            if not cid or int(cid) > 0:
                continue
            try:
                ok = await admin_cache.bot_can_restrict(bot, int(cid))
                checked += 1
                if not ok:
                    logger.warning(
                        "Bot lacks restrict rights in chat %s (%s). "
                        "Promote the bot to admin with Ban users permission.",
                        cid,
                        row.get("title") or "?",
                    )
            except Exception:
                pass
        if checked:
            logger.info("Rights check done for %s group(s)", checked)
        logger.info("Bot @%s id=%s", me.username, me.id)
    except Exception as e:
        logger.debug("rights check skip: %s", e)


async def main() -> None:
    if not config.BOT_TOKEN:
        raise SystemExit(
            "Нет BOT_TOKEN. Скопируй .env.example в .env и вставь токен от @BotFather.\n"
            "Также укажи BOT_ADMINS=твой_telegram_id"
        )
    await init_db()
    logger.info("DB ready · TitanMod %s · commands in catalog: %s", config.VERSION, len(ALL_COMMAND_NAMES))

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML), timeout=60)
    dp = Dispatcher(storage=MemoryStorage())

    # dp.message.outer_middleware(AliasMiddleware())
    dp.message.middleware(ContextMiddleware())
    dp.callback_query.middleware(ContextMiddleware())
    # dp.message.middleware(GroupActivationMiddleware())
    # dp.message.middleware(AntiCheatMiddleware())
    # dp.message.middleware(DisableCommandMiddleware())
    # dp.message.middleware(AntiFloodMiddleware())
    # dp.message.middleware(SnipeTrackMiddleware())

    routers = (
        catalog.router, cabinet.router, ranks.router, economy.router,
        start.router, owner.router, punish.router, warns.router, locks.router,
        welcome.router, notes.router, filters_cmd.router, federation.router,
        security.router, admin_tools.router, settings.router, info.router,
        extras.router, fun.router, more.router, levels.router, giveaway.router,
        topics.router, quarantine.router, aliases.router, mass.router,
        backup.router, watch.router, tickets.router,
        pack_utils.router, pack_fun.router, pack_reports.router, pack_economy.router,
        activate.router, security_ac.router, stats_ui.router, minigames.router, extra_pack.router, new_cmds.router, v42_tools.router, full_cmds.router, v45.router, synonyms.router,
    )
    for r in routers:
        dp.include_router(r)
    dp.include_router(moderation.router)

    asyncio.create_task(scheduler_loop(bot))
    from handlers.catalog import setup_bot_commands
    await setup_bot_commands(bot)
    await _warn_if_bot_lacks_rights(bot)

    logger.info("TitanMod %s polling…", config.VERSION)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        try:
            import aiosqlite
            from database.db import DB_PATH

            async with aiosqlite.connect(DB_PATH) as _db:
                await _db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                await _db.commit()
            logger.info("DB checkpoint OK (%s)", DB_PATH)
        except Exception as e:
            logger.warning("DB checkpoint: %s", e)
        await bot.session.close()

from aiogram.exceptions import TelegramBadRequest
import logging

@dp.errors()
async def global_error_handler(update, exception):
    logging.error(f"Update error: {exception}")
    if isinstance(exception, TelegramBadRequest) and "TOPIC" in str(exception).upper():
        # Тема закрыта — пробуем отправить в General
        try:
            if update.message:
                await update.message.bot.send_message(
                    chat_id=update.message.chat.id,
                    text="⚠️ Тема закрыта. Откройте её или пишите в General.",
                )
        except Exception:
            pass
    return True

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("stopped")
