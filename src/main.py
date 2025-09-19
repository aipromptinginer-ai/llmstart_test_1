"""Точка входа в приложение."""
import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config.settings import load_config
from bot.handlers import router, init_llm
from bot.middleware import ErrorHandlingMiddleware, MetricsMiddleware


async def main() -> None:
    """Главная функция запуска бота."""
    # Настройка базового логирования в stdout согласно @vision.md раздел 11
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        # Загрузка и валидация конфигурации
        logger.info("Loading configuration...")
        config = load_config()
        logger.info("Configuration loaded successfully")
        
        # Создание бота и диспетчера
        logger.info("Initializing bot...")
        bot = Bot(
            token=config.telegram_bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML)
        )
        
        # Валидация токена через проверку bot info
        try:
            bot_info = await bot.get_me()
            logger.info(f"Bot @{bot_info.username} connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Telegram API: {e}")
            raise ValueError("Недействительный TELEGRAM_BOT_TOKEN или проблемы с подключением к Telegram API")
        
        # Инициализация LLM
        logger.info("Initializing LLM...")
        await init_llm(config)
        logger.info("LLM initialized successfully")
        
        # Настройка диспетчера с middleware
        dp = Dispatcher()
        
        # Добавление middleware для обработки ошибок и метрик
        dp.message.middleware(ErrorHandlingMiddleware())
        dp.message.middleware(MetricsMiddleware())
        
        dp.include_router(router)
        
        logger.info("Starting bot polling...")
        await dp.start_polling(bot)
        
    except Exception as e:
        logger.error(f"Failed to start bot: {e}")
        raise
    finally:
        # Закрытие сессии бота
        if 'bot' in locals():
            await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
