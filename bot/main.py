"""Bot main entrypoint."""
import asyncio
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis

from bot.core.config import bot_settings
from bot.core.logging_config import setup_logging, get_logger
from bot.middlewares.auth import AuthMiddleware
from bot.middlewares.i18n import setup_i18n_middleware
from bot.routers import routers_list

# Setup logging
setup_logging()
logger = get_logger(__name__)


async def on_startup(bot: Bot):
    """Bot startup callback.
    
    Args:
        bot: Bot instance
    """
    logger.info("Bot is starting up...")
    
    # Get bot info
    bot_info = await bot.get_me()
    logger.info(f"Bot username: @{bot_info.username}")
    logger.info(f"Bot ID: {bot_info.id}")
    
    # Set bot commands
    from aiogram.types import BotCommand
    commands = [
        BotCommand(command="start", description="Главное меню / Main menu"),
        BotCommand(command="help", description="Помощь / Help"),
        BotCommand(command="cancel", description="Отменить операцию / Cancel operation"),
    ]
    await bot.set_my_commands(commands)
    
    logger.info("Bot startup complete")


async def on_shutdown(bot: Bot, dp: Dispatcher):
    """Bot shutdown callback.
    
    Args:
        bot: Bot instance
        dp: Dispatcher instance
    """
    logger.info("Bot is shutting down...")
    
    # Close API clients if any are stored
    # Close storage
    await dp.storage.close()
    
    logger.info("Bot shutdown complete")


async def main():
    """Main bot entrypoint."""
    logger.info("=" * 50)
    logger.info("USE.NET Proxy Shop Bot")
    logger.info("=" * 50)
    
    # Initialize Bot
    bot = Bot(token=bot_settings.TELEGRAM_BOT_TOKEN, parse_mode="HTML")
    
    # Initialize Redis storage
    redis = Redis.from_url(bot_settings.REDIS_URL)
    storage = RedisStorage(redis=redis)
    
    # Initialize Dispatcher
    dp = Dispatcher(storage=storage)
    
    # Setup startup and shutdown callbacks
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    
    # Setup middlewares
    # i18n middleware should be before auth middleware
    i18n_middleware = setup_i18n_middleware()
    dp.update.middleware(i18n_middleware)
    
    # Auth middleware
    auth_middleware = AuthMiddleware()
    dp.update.middleware(auth_middleware)
    
    logger.info("Middlewares registered")
    
    # Include routers
    for router in routers_list:
        dp.include_router(router)
        logger.info(f"Router '{router.name}' registered")
    
    logger.info(f"Total {len(routers_list)} routers registered")
    
    # Start polling
    try:
        logger.info("Starting bot polling...")
        await dp.start_polling(
            bot,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
    except KeyboardInterrupt:
        logger.info("Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"Bot error: {e}", exc_info=True)
    finally:
        # Cleanup
        await on_shutdown(bot, dp)
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")
        sys.exit(0)
