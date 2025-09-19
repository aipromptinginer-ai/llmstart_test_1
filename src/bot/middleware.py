"""Middleware для обработки ошибок и метрик."""
import logging
import time
from typing import Callable, Any, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, TelegramObject

from monitoring.metrics import metrics_collector

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware(BaseMiddleware):
    """Middleware для централизованной обработки ошибок."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка запроса с перехватом ошибок."""
        start_time = time.time()
        
        try:
            # Выполнение основного обработчика
            result = await handler(event, data)
            
            # Запись успешной метрики для сообщений
            if isinstance(event, Message) and event.text:
                response_time = time.time() - start_time
                metrics_collector.record_message(
                    user_id=event.from_user.id,
                    message_length=len(event.text),
                    processed=True
                )
                logger.debug(f"Message processed successfully in {response_time:.2f}s")
            
            return result
            
        except Exception as e:
            # Обработка ошибок
            response_time = time.time() - start_time
            error_message = self._get_user_friendly_error(e)
            
            logger.error(f"Error in handler: {e}", exc_info=True)
            
            # Запись метрики ошибки
            if isinstance(event, Message):
                metrics_collector.record_message(
                    user_id=event.from_user.id,
                    message_length=len(event.text) if event.text else 0,
                    processed=False
                )
                
                # Отправка пользователю понятного сообщения об ошибке
                try:
                    await event.answer(error_message)
                except Exception as send_error:
                    logger.error(f"Failed to send error message to user: {send_error}")
            
            # Не пробрасываем исключение дальше, чтобы не крашить бота
            return None
    
    def _get_user_friendly_error(self, error: Exception) -> str:
        """Преобразование технических ошибок в понятные пользователю сообщения."""
        error_type = type(error).__name__
        
        # Словарь соответствий технических ошибок и пользовательских сообщений
        error_messages = {
            'LLMError': 'Сервис ИИ временно недоступен. Попробуйте повторить запрос через несколько минут.',
            'ConnectionError': 'Проблемы с подключением к сервису. Проверьте интернет-соединение.',
            'TimeoutError': 'Превышено время ожидания ответа. Попробуйте еще раз.',
            'ValueError': 'Некорректные данные в запросе. Проверьте формат сообщения.',
            'KeyError': 'Внутренняя ошибка конфигурации. Обратитесь к администратору.',
            'PermissionError': 'Недостаточно прав для выполнения операции.',
            'FileNotFoundError': 'Служебные файлы не найдены. Обратитесь к администратору.',
        }
        
        # Возвращаем специфичное сообщение или общее
        return error_messages.get(error_type, 
            'Произошла внутренняя ошибка. Пожалуйста, попробуйте позже или обратитесь к администратору.')


class MetricsMiddleware(BaseMiddleware):
    """Middleware для сбора метрик LLM запросов."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Any],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Сбор метрик для LLM запросов."""
        start_time = time.time()
        success = False
        model = "unknown"
        error_type = ""
        
        try:
            result = await handler(event, data)
            success = True
            return result
            
        except Exception as e:
            error_type = type(e).__name__
            raise
            
        finally:
            # Запись метрики LLM запроса
            response_time = time.time() - start_time
            
            # Попытка определить модель из контекста
            if 'config' in data:
                config = data['config']
                model = getattr(config, 'primary_model', 'unknown')
            
            metrics_collector.record_llm_request(
                success=success,
                model=model,
                response_time=response_time,
                error_type=error_type
            )