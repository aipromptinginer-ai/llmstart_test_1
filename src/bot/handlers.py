"""Обработчики сообщений Telegram бота."""
import logging
import asyncio
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from llm.client import create_llm_client, generate_response_with_history, LLMError
from llm.prompts import load_system_prompt
from config.settings import Config
from memory.storage import get_user_session, add_message, get_user_history, start_cleanup_task
from monitoring.metrics import metrics_collector

logger = logging.getLogger(__name__)
router = Router()

# Глобальные переменные для LLM
llm_client = None
system_prompt = None
config = None


async def init_llm(app_config: Config) -> None:
    """Инициализация LLM клиента."""
    global llm_client, system_prompt, config
    logger.info("Initializing LLM client...")
    
    config = app_config
    llm_client = await create_llm_client(config.openrouter_api_key)
    system_prompt = load_system_prompt()
    
    # Запуск фоновой задачи очистки памяти
    import asyncio
    asyncio.create_task(start_cleanup_task(
        cleanup_interval_hours=config.cleanup_interval_hours,
        ttl_hours=config.memory_ttl_hours
    ))
    
    # Запуск периодического логирования статистики
    if config.log_hourly_stats:
        asyncio.create_task(start_hourly_stats_logging())
    
    logger.info("LLM client and memory cleanup task initialized successfully")


async def start_hourly_stats_logging() -> None:
    """Запуск периодического логирования статистики каждый час."""
    while True:
        try:
            await asyncio.sleep(3600)  # Ждем час
            metrics_collector.log_hourly_stats()
        except Exception as e:
            logger.error(f"Error in hourly stats logging: {e}")


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_name = message.from_user.first_name or "друг"
    user_id = message.from_user.id
    
    # Создание/получение сессии для сохранения в памяти
    session = get_user_session(user_id, user_name)
    
    welcome_text = f"""Добро пожаловать, {user_name}! 👋

Я - ваш ИИ-консультант по формулировке целей обучения.

🎯 Помогаю составлять учебные цели по таксономии Блума:
• Знание (запоминание фактов)
• Понимание (объяснение концепций)  
• Применение (использование на практике)
• Анализ (разбор на части)
• Синтез (создание нового)
• Оценка (критическое мышление)

📝 Просто опишите тематику занятия и ожидаемые результаты обучения.

Для получения примеров используйте команду /help"""
    
    # Сохранение команды и ответа в историю диалога
    add_message(user_id, "user", "/start", config.max_history_size)
    add_message(user_id, "assistant", welcome_text, config.max_history_size)
    
    await message.answer(welcome_text)
    logger.info(f"Команда /start от пользователя {user_id}, сохранена в историю")


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Обработчик команды /help."""
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "пользователь"
    
    # Создание/получение сессии для сохранения в памяти
    session = get_user_session(user_id, user_name)
    
    help_text = """📖 Примеры вопросов:

"Помогите сформулировать цели обучения по основам промышленной безопасности в соответствии с законодательством. Обучаемый должен уметь воспроизводить полученную информацию."

"Нужны цели для практического занятия по использованию огнетушителя ОУ. Обучаемые должны уметь применять на практике полученные знания."

"Как составить цели обучения для аудиторного занятия по теме - Порядок действий при пожаре. Обучаемые должны объяснить своими словами, обобщить или пересказать."

💡 Укажите:
• Тематику занятия
• Целевую аудиторию (возраст, уровень подготовки)
• Желаемый уровень по Блуму
• Продолжительность обучения"""
    
    # Сохранение команды и ответа в историю диалога
    add_message(user_id, "user", "/help", config.max_history_size)
    add_message(user_id, "assistant", help_text, config.max_history_size)
    
    await message.answer(help_text)
    logger.info(f"Команда /help от пользователя {user_id}, сохранена в историю")


@router.message()
async def handle_message(message: Message) -> None:
    """Обработчик текстовых сообщений с LLM и памятью диалога."""
    user_text = message.text
    user_id = message.from_user.id
    user_name = message.from_user.first_name or "пользователь"
    
    logger.info(f"Сообщение от пользователя {user_id}, длина: {len(user_text)}")
    
    # Проверка инициализации LLM
    if not llm_client or not system_prompt or not config:
        logger.error("LLM client not initialized")
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
        return
    
    # Проверка длины сообщения
    if len(user_text) > config.max_message_length:
        logger.warning(f"Message too long from user {user_id}: {len(user_text)} chars")
        metrics_collector.record_message(user_id, len(user_text), processed=False)
        await message.answer(f"Сообщение слишком длинное. Максимум {config.max_message_length} символов.")
        return
    
    try:
        # Получение/создание сессии пользователя
        session = get_user_session(user_id, user_name)
        
        # Получение истории диалога для LLM
        history = get_user_history(user_id)
        
        # Добавление пользовательского сообщения в историю
        add_message(user_id, "user", user_text, config.max_history_size)
        
        # Генерация ответа с учетом истории
        logger.info(f"Generating LLM response with history for user {user_id} ({len(history)} messages)")
        
        response = await generate_response_with_history(
            client=llm_client,
            system_prompt=system_prompt,
            user_message=user_text,
            message_history=history,
            primary_model=config.primary_model,
            fallback_model=config.fallback_model,
            retry_attempts=config.retry_attempts,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p
        )
        
        # Добавление ответа ассистента в историю
        add_message(user_id, "assistant", response, config.max_history_size)
        
        # Запись метрики успешного сообщения
        metrics_collector.record_message(user_id, len(user_text), processed=True)
        
        await message.answer(response)
        logger.info(f"LLM response with history sent to user {user_id}")
        
    except LLMError as e:
        logger.error(f"LLM error for user {user_id}: {e}")
        metrics_collector.record_message(user_id, len(user_text), processed=False)
        error_message = "Извините, сервис временно недоступен. Попробуйте повторить запрос через несколько минут."
        await message.answer(error_message)
        
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        metrics_collector.record_message(user_id, len(user_text), processed=False)
        await message.answer("Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.")
