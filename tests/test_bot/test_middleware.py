"""Тесты middleware бота."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat
from src.bot.middleware import ErrorHandlingMiddleware, MetricsMiddleware


class TestErrorHandlingMiddleware:
    """Тесты middleware обработки ошибок."""
    
    def create_mock_message(self, text="Test message", user_id=123):
        """Создание мок-объекта сообщения."""
        user = User(id=user_id, is_bot=False, first_name="TestUser")
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            content_type="text",
            text=text
        )
        return message
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_success(self):
        """Тест успешной обработки без ошибок."""
        middleware = ErrorHandlingMiddleware()
        message = self.create_mock_message("Test message")
        
        async def handler(event, data):
            return "Success"
        
        result = await middleware(handler, message, {})
        
        assert result == "Success"
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_with_error(self):
        """Тест обработки с ошибкой."""
        middleware = ErrorHandlingMiddleware()
        message = self.create_mock_message("Test message")
        
        async def handler(event, data):
            raise Exception("Test error")
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics:
            result = await middleware(handler, message, {})
            
            # Проверяем что ошибка была обработана
            assert result is None
            
            # Проверяем что метрика была записана
            mock_metrics.record_message.assert_called_once_with(123, 12, False)
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_send_error_fails(self):
        """Тест когда отправка сообщения об ошибке тоже падает."""
        middleware = ErrorHandlingMiddleware()
        message = self.create_mock_message("Test message")
        message.answer.side_effect = Exception("Send failed")
        
        async def handler(event, data):
            raise Exception("Test error")
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics, \
             patch('src.bot.middleware.logger') as mock_logger:
            
            result = await middleware(handler, message, {})
            
            # Проверяем что ошибка была обработана
            assert result is None
            
            # Проверяем что была попытка отправить сообщение об ошибке
            message.answer.assert_called_once()
            
            # Проверяем что ошибка отправки была залогирована
            mock_logger.error.assert_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_middleware_non_message_event(self):
        """Тест обработки события, не являющегося сообщением."""
        middleware = ErrorHandlingMiddleware()
        event = MagicMock()  # Не Message объект
        
        async def handler(event, data):
            raise Exception("Test error")
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics:
            result = await middleware(handler, event, {})
            
            # Проверяем что ошибка была обработана
            assert result is None
            
            # Проверяем что метрика НЕ была записана (не сообщение)
            mock_metrics.record_message.assert_not_called()
    
    def test_get_user_friendly_error(self):
        """Тест преобразования технических ошибок в понятные сообщения."""
        middleware = ErrorHandlingMiddleware()
        
        # Тест различных типов ошибок
        test_cases = [
            (Exception("LLMError"), "Произошла внутренняя ошибка. Пожалуйста, попробуйте позже или обратитесь к администратору."),
            (ConnectionError("Connection failed"), "Проблемы с подключением к сервису. Проверьте интернет-соединение."),
            (TimeoutError("Timeout"), "Превышено время ожидания ответа. Попробуйте еще раз."),
            (ValueError("Invalid value"), "Некорректные данные в запросе. Проверьте формат сообщения."),
            (KeyError("Missing key"), "Внутренняя ошибка конфигурации. Обратитесь к администратору."),
            (PermissionError("No permission"), "Недостаточно прав для выполнения операции."),
            (FileNotFoundError("File not found"), "Служебные файлы не найдены. Обратитесь к администратору."),
        ]
        
        for error, expected_message in test_cases:
            result = middleware._get_user_friendly_error(error)
            assert result == expected_message


class TestMetricsMiddleware:
    """Тесты middleware сбора метрик."""
    
    def create_mock_message(self, text="Test message", user_id=123):
        """Создание мок-объекта сообщения."""
        user = User(id=user_id, is_bot=False, first_name="TestUser")
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            content_type="text",
            text=text
        )
        return message
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_success(self):
        """Тест успешного сбора метрик."""
        middleware = MetricsMiddleware()
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.primary_model = "test-model"
        data = {"config": mock_config}
        
        async def handler(event, data):
            return "Success"
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics, \
             patch('src.bot.middleware.time') as mock_time:
            
            mock_time.time.side_effect = [1000.0, 1001.5]  # start_time, end_time
            
            result = await middleware(handler, message, data)
            
            assert result == "Success"
            
            # Проверяем что метрика была записана
            mock_metrics.record_llm_request.assert_called_once_with(
                success=True,
                model="test-model",
                response_time=1.5,
                error_type=""
            )
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_with_error(self):
        """Тест сбора метрик при ошибке."""
        middleware = MetricsMiddleware()
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.primary_model = "test-model"
        data = {"config": mock_config}
        
        async def handler(event, data):
            raise ValueError("Test error")
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics, \
             patch('src.bot.middleware.time') as mock_time:
            
            mock_time.time.side_effect = [1000.0, 1001.0]  # start_time, end_time
            
            with pytest.raises(ValueError, match="Test error"):
                await middleware(handler, message, data)
            
            # Проверяем что метрика была записана
            mock_metrics.record_llm_request.assert_called_once_with(
                success=False,
                model="test-model",
                response_time=1.0,
                error_type="ValueError"
            )
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_no_config(self):
        """Тест сбора метрик без конфигурации."""
        middleware = MetricsMiddleware()
        message = self.create_mock_message("Test message")
        data = {}  # Нет конфигурации
        
        async def handler(event, data):
            return "Success"
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics, \
             patch('src.bot.middleware.time') as mock_time:
            
            mock_time.time.side_effect = [1000.0, 1001.0]
            
            result = await middleware(handler, message, data)
            
            assert result == "Success"
            
            # Проверяем что метрика была записана с моделью по умолчанию
            mock_metrics.record_llm_request.assert_called_once_with(
                success=True,
                model="unknown",
                response_time=1.0,
                error_type=""
            )
    
    @pytest.mark.asyncio
    async def test_metrics_middleware_response_time_calculation(self):
        """Тест расчета времени ответа."""
        middleware = MetricsMiddleware()
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.primary_model = "test-model"
        data = {"config": mock_config}
        
        async def handler(event, data):
            return "Success"
        
        with patch('src.bot.middleware.metrics_collector') as mock_metrics, \
             patch('src.bot.middleware.time') as mock_time:
            
            # Симулируем время выполнения 2.5 секунды
            mock_time.time.side_effect = [1000.0, 1002.5]
            
            result = await middleware(handler, message, data)
            
            assert result == "Success"
            
            # Проверяем что время ответа рассчитано правильно
            mock_metrics.record_llm_request.assert_called_once_with(
                success=True,
                model="test-model",
                response_time=2.5,
                error_type=""
            )
