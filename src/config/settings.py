"""Настройки приложения из переменных окружения."""
import os
import logging
from dataclasses import dataclass
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


@dataclass
class Config:
    """Конфигурация приложения."""
    telegram_bot_token: str
    openrouter_api_key: str
    primary_model: str = "meta-llama/llama-3.1-8b-instruct:free"
    fallback_model: str = "meta-llama/llama-3.2-3b-instruct:free"
    temperature: float = 0.7
    max_tokens: int = 1500
    top_p: float = 0.9
    retry_attempts: int = 3
    max_message_length: int = 1000
    memory_ttl_hours: int = 24
    max_history_size: int = 10
    cleanup_interval_hours: int = 6
    enable_metrics: bool = True
    metrics_cleanup_hours: int = 24
    log_hourly_stats: bool = True


def load_config() -> Config:
    """Загрузка конфигурации из переменных окружения."""
    load_dotenv()
    logger.info("Loading configuration from environment variables")
    
    config = Config(
        telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY", ""),
        primary_model=os.getenv("PRIMARY_MODEL", "meta-llama/llama-3.1-8b-instruct:free"),
        fallback_model=os.getenv("FALLBACK_MODEL", "meta-llama/llama-3.2-3b-instruct:free"),
        temperature=float(os.getenv("TEMPERATURE", "0.7")),
        max_tokens=int(os.getenv("MAX_TOKENS", "1500")),
        top_p=float(os.getenv("TOP_P", "0.9")),
        retry_attempts=int(os.getenv("RETRY_ATTEMPTS", "3")),
        max_message_length=int(os.getenv("MAX_MESSAGE_LENGTH", "1000")),
        memory_ttl_hours=int(os.getenv("MEMORY_TTL_HOURS", "24")),
        max_history_size=int(os.getenv("MAX_HISTORY_SIZE", "10")),
        cleanup_interval_hours=int(os.getenv("CLEANUP_INTERVAL_HOURS", "6")),
        enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
        metrics_cleanup_hours=int(os.getenv("METRICS_CLEANUP_HOURS", "24")),
        log_hourly_stats=os.getenv("LOG_HOURLY_STATS", "true").lower() == "true"
    )
    
    validate_config(config)
    logger.info("Configuration loaded and validated successfully")
    return config


def validate_config(config: Config) -> None:
    """Валидация конфигурации при запуске."""
    logger.info("Validating configuration...")
    
    # Проверка обязательных токенов
    if not config.telegram_bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN не установлен в переменных окружения")
    if not config.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY не установлен в переменных окружения")
    
    # Проверка диапазонов значений
    if not (0.0 <= config.temperature <= 2.0):
        raise ValueError(f"TEMPERATURE должна быть от 0.0 до 2.0, получено: {config.temperature}")
    if config.max_tokens <= 0:
        raise ValueError(f"MAX_TOKENS должен быть > 0, получено: {config.max_tokens}")
    if not (0.0 <= config.top_p <= 1.0):
        raise ValueError(f"TOP_P должен быть от 0.0 до 1.0, получено: {config.top_p}")
    if config.retry_attempts <= 0:
        raise ValueError(f"RETRY_ATTEMPTS должен быть > 0, получено: {config.retry_attempts}")
    if config.max_message_length <= 0:
        raise ValueError(f"MAX_MESSAGE_LENGTH должен быть > 0, получено: {config.max_message_length}")
    if config.memory_ttl_hours <= 0:
        raise ValueError(f"MEMORY_TTL_HOURS должен быть > 0, получено: {config.memory_ttl_hours}")
    if config.max_history_size <= 0:
        raise ValueError(f"MAX_HISTORY_SIZE должен быть > 0, получено: {config.max_history_size}")
    if config.cleanup_interval_hours <= 0:
        raise ValueError(f"CLEANUP_INTERVAL_HOURS должен быть > 0, получено: {config.cleanup_interval_hours}")
    if config.metrics_cleanup_hours <= 0:
        raise ValueError(f"METRICS_CLEANUP_HOURS должен быть > 0, получено: {config.metrics_cleanup_hours}")
    
    logger.info("Configuration validation completed successfully")
