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
from services.scheduler import scheduler_loop
from services.locks import OUR_COMMANDS
from core.commands import ALL_COMMAND_NAMES
from handlers import (
    start, punish, warns, locks, welcome, notes, filters_cmd, federation,
    security, admin_tools, settings, info, extras, fun, owner, more, moderation,
    levels, giveaway, topics, quarantine, aliases, mass, backup, watch, catalog,
)

logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("titanmod")
OUR_COMMANDS.update(ALL_COMMAND_NAMES)


async def main():
    if not config.BOT_TOKEN:
        raise SystemExit(
            "Нет BOT_TOKEN. Скопируй .env.example в .env и вставь токен от @BotFather."
        )
    await init_db()
    logger.info("DB ready")

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    dp.message.outer_middleware(AliasMiddleware())
    dp.message.middleware(ContextMiddleware())
    dp.callback_query.middleware(ContextMiddleware())
    dp.message.middleware(DisableCommandMiddleware())
    dp.message.middleware(AntiFloodMiddleware())

    for r in (
        catalog.router, start.router, owner.router, punish.router, warns.router, locks.router,
        welcome.router, notes.router, filters_cmd.router, federation.router,
        security.router, admin_tools.router, settings.router, info.router,
        extras.router, fun.router, more.router, levels.router, giveaway.router,
        topics.router, quarantine.router, aliases.router, mass.router,
        backup.router, watch.router,
    ):
        dp.include_router(r)
    dp.include_router(moderation.router)

    asyncio.create_task(scheduler_loop(bot))
    from handlers.catalog import setup_bot_commands
    await setup_bot_commands(bot)
    logger.info("TitanMod %s polling…", config.VERSION)
    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("stopped")
