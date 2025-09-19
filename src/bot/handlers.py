"""Обработчики сообщений Telegram бота."""
import logging
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from llm.client import create_llm_client, generate_response, LLMError
from llm.prompts import load_system_prompt
from config.settings import Config

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
    
    logger.info("LLM client initialized successfully")


@router.message(Command("start"))
async def handle_start(message: Message) -> None:
    """Обработчик команды /start."""
    user_name = message.from_user.first_name or "друг"
    user_id = message.from_user.id
    
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
    
    await message.answer(welcome_text)
    logger.info(f"Команда /start от пользователя {user_id}")


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    """Обработчик команды /help."""
    user_id = message.from_user.id
    
    help_text = """📖 Примеры вопросов:

"Помогите сформулировать цели обучения по основам промышленной безопасности в соответствии с законодательством. Обучаемый должен уметь воспроизводить полученную информацию."

"Нужны цели для практического занятия по использованию огнетушителя ОУ. Обучаемые должны уметь применять на практике полученные знания."

"Как составить цели обучения для аудиторного занятия по теме - Порядок действий при пожаре. Обучаемые должны объяснить своими словами, обобщить или пересказать."

💡 Укажите:
• Тематику занятия
• Целевую аудиторию (возраст, уровень подготовки)
• Желаемый уровень по Блуму
• Продолжительность обучения"""
    
    await message.answer(help_text)
    logger.info(f"Команда /help от пользователя {user_id}")


@router.message()
async def handle_message(message: Message) -> None:
    """Обработчик текстовых сообщений с LLM."""
    user_text = message.text
    user_id = message.from_user.id
    
    logger.info(f"Сообщение от пользователя {user_id}, длина: {len(user_text)}")
    
    # Проверка инициализации LLM
    if not llm_client or not system_prompt or not config:
        logger.error("LLM client not initialized")
        await message.answer("Сервис временно недоступен. Попробуйте позже.")
        return
    
    # Проверка длины сообщения
    if len(user_text) > config.max_message_length:
        logger.warning(f"Message too long from user {user_id}: {len(user_text)} chars")
        await message.answer(f"Сообщение слишком длинное. Максимум {config.max_message_length} символов.")
        return
    
    try:
        # Генерация ответа через LLM
        logger.info(f"Generating LLM response for user {user_id}")
        
        response = await generate_response(
            client=llm_client,
            system_prompt=system_prompt,
            user_message=user_text,
            primary_model=config.primary_model,
            fallback_model=config.fallback_model,
            retry_attempts=config.retry_attempts,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p
        )
        
        await message.answer(response)
        logger.info(f"LLM response sent to user {user_id}")
        
    except LLMError as e:
        logger.error(f"LLM error for user {user_id}: {e}")
        error_message = "Извините, сервис временно недоступен. Попробуйте повторить запрос через несколько минут."
        await message.answer(error_message)
        
    except Exception as e:
        logger.error(f"Unexpected error for user {user_id}: {e}")
        await message.answer("Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.")
