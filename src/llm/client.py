"""Клиент для работы с OpenRouter API."""
import logging
import asyncio
from openai import AsyncOpenAI
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class LLMError(Exception):
    """Исключение для ошибок LLM."""
    pass


async def create_llm_client(api_key: str, base_url: str = "https://openrouter.ai/api/v1") -> AsyncOpenAI:
    """Создание асинхронного клиента OpenRouter."""
    logger.info("Creating LLM client for OpenRouter API")
    return AsyncOpenAI(
        api_key=api_key,
        base_url=base_url
    )


async def send_request(
    client: AsyncOpenAI,
    messages: List[Dict[str, str]],
    model: str,
    temperature: float = 0.7,
    max_tokens: int = 1500,
    top_p: float = 0.9
) -> str:
    """Отправка запроса к LLM модели."""
    try:
        logger.info(f"Sending request to model {model}")
        
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            timeout=30.0
        )
        
        content = response.choices[0].message.content
        if not content:
            raise LLMError("Пустой ответ от LLM")
            
        logger.info(f"LLM response received, length: {len(content)}")
        return content
        
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        raise LLMError(f"Ошибка запроса к LLM: {e}")


async def generate_response(
    client: AsyncOpenAI,
    system_prompt: str,
    user_message: str,
    primary_model: str,
    fallback_model: str,
    retry_attempts: int = 3,
    **llm_params
) -> str:
    """Генерация ответа с retry-логикой и fallback (без истории)."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]
    
    # Попытки с основной моделью
    for attempt in range(retry_attempts):
        try:
            return await send_request(client, messages, primary_model, **llm_params)
        except LLMError as e:
            logger.warning(f"Primary model attempt {attempt + 1} failed: {e}")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
    
    # Fallback на резервную модель
    logger.warning(f"Switching to fallback model: {fallback_model}")
    try:
        return await send_request(client, messages, fallback_model, **llm_params)
    except LLMError as e:
        logger.error(f"Fallback model failed: {e}")
        raise LLMError("Все модели LLM недоступны. Попробуйте позже.")


async def generate_response_with_history(
    client: AsyncOpenAI,
    system_prompt: str,
    user_message: str,
    message_history: List[Dict[str, str]],
    primary_model: str,
    fallback_model: str,
    retry_attempts: int = 3,
    **llm_params
) -> str:
    """Генерация ответа с учетом истории диалога."""
    # Формирование полного контекста
    messages = [{"role": "system", "content": system_prompt}]
    
    # Добавление истории диалога
    messages.extend(message_history)
    
    # Добавление нового сообщения пользователя
    messages.append({"role": "user", "content": user_message})
    
    logger.debug(f"Generating response with {len(message_history)} history messages")
    
    # Попытки с основной моделью
    for attempt in range(retry_attempts):
        try:
            return await send_request(client, messages, primary_model, **llm_params)
        except LLMError as e:
            logger.warning(f"Primary model attempt {attempt + 1} failed: {e}")
            if attempt < retry_attempts - 1:
                await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
    
    # Fallback на резервную модель
    logger.warning(f"Switching to fallback model: {fallback_model}")
    try:
        return await send_request(client, messages, fallback_model, **llm_params)
    except LLMError as e:
        logger.error(f"Fallback model failed: {e}")
        raise LLMError("Все модели LLM недоступны. Попробуйте позже.")
