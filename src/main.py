"""Точка входа в приложение."""
import logging


def main():
    """Главная функция запуска бота."""
    # Настройка базового логирования в stdout согласно @vision.md раздел 11
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Bot starting...")
    # TODO: Здесь будет инициализация бота в следующих итерациях
    logger.info("Bot setup completed")


if __name__ == "__main__":
    main()
