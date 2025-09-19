"""Тесты обработчиков бота."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat
from src.bot.handlers import init_llm, handle_start, handle_help, handle_message


class TestInitLLM:
    """Тесты инициализации LLM."""
    
    @pytest.mark.asyncio
    async def test_init_llm_success(self):
        """Тест успешной инициализации LLM."""
        mock_config = MagicMock()
        mock_config.openrouter_api_key = "test_key"
        mock_config.cleanup_interval_hours = 6
        mock_config.memory_ttl_hours = 24
        mock_config.log_hourly_stats = False
        
        with patch('src.bot.handlers.create_llm_client') as mock_create_client, \
             patch('src.bot.handlers.load_system_prompt') as mock_load_prompt, \
             patch('src.bot.handlers.start_cleanup_task') as mock_cleanup, \
             patch('src.bot.handlers.start_hourly_stats_logging') as mock_stats:
            
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            mock_load_prompt.return_value = "Test prompt"
            
            await init_llm(mock_config)
            
            mock_create_client.assert_called_once_with("test_key")
            mock_load_prompt.assert_called_once()
            mock_cleanup.assert_called_once_with(6, 24)
            mock_stats.assert_not_called()  # log_hourly_stats = False
    
    @pytest.mark.asyncio
    async def test_init_llm_with_stats_logging(self):
        """Тест инициализации LLM с логированием статистики."""
        mock_config = MagicMock()
        mock_config.openrouter_api_key = "test_key"
        mock_config.cleanup_interval_hours = 6
        mock_config.memory_ttl_hours = 24
        mock_config.log_hourly_stats = True
        
        with patch('src.bot.handlers.create_llm_client') as mock_create_client, \
             patch('src.bot.handlers.load_system_prompt') as mock_load_prompt, \
             patch('src.bot.handlers.start_cleanup_task') as mock_cleanup, \
             patch('src.bot.handlers.start_hourly_stats_logging') as mock_stats:
            
            mock_client = AsyncMock()
            mock_create_client.return_value = mock_client
            mock_load_prompt.return_value = "Test prompt"
            
            await init_llm(mock_config)
            
            mock_stats.assert_called_once()


class TestHandleStart:
    """Тесты обработчика команды /start."""
    
    def create_mock_message(self, user_id=123, first_name="TestUser"):
        """Создание мок-объекта сообщения."""
        user = User(id=user_id, is_bot=False, first_name=first_name)
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            content_type="text",
            text="/start"
        )
        return message
    
    @pytest.mark.asyncio
    async def test_handle_start_success(self):
        """Тест успешной обработки команды /start."""
        message = self.create_mock_message(123, "TestUser")
        
        with patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.add_message') as mock_add_message, \
             patch('src.bot.handlers.config') as mock_config:
            
            mock_config.max_history_size = 10
            mock_session = {"user_id": 123, "user_name": "TestUser"}
            mock_get_session.return_value = mock_session
            
            await handle_start(message)
            
            # Проверяем что сессия была создана
            mock_get_session.assert_called_once_with(123, "TestUser")
            
            # Проверяем что сообщения были добавлены в историю
            assert mock_add_message.call_count == 2
            mock_add_message.assert_any_call(123, "user", "/start", 10)
            mock_add_message.assert_any_call(123, "assistant", 
                "Добро пожаловать, TestUser! 👋", 10)
    
    @pytest.mark.asyncio
    async def test_handle_start_without_first_name(self):
        """Тест обработки команды /start без имени пользователя."""
        message = self.create_mock_message(123, None)
        
        with patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.add_message') as mock_add_message, \
             patch('src.bot.handlers.config') as mock_config:
            
            mock_config.max_history_size = 10
            mock_session = {"user_id": 123, "user_name": "друг"}
            mock_get_session.return_value = mock_session
            
            await handle_start(message)
            
            # Проверяем что использовалось имя по умолчанию
            mock_get_session.assert_called_once_with(123, "друг")


class TestHandleHelp:
    """Тесты обработчика команды /help."""
    
    def create_mock_message(self, user_id=123, first_name="TestUser"):
        """Создание мок-объекта сообщения."""
        user = User(id=user_id, is_bot=False, first_name=first_name)
        chat = Chat(id=user_id, type="private")
        message = Message(
            message_id=1,
            date=1234567890,
            chat=chat,
            from_user=user,
            content_type="text",
            text="/help"
        )
        return message
    
    @pytest.mark.asyncio
    async def test_handle_help_success(self):
        """Тест успешной обработки команды /help."""
        message = self.create_mock_message(123, "TestUser")
        
        with patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.add_message') as mock_add_message, \
             patch('src.bot.handlers.config') as mock_config:
            
            mock_config.max_history_size = 10
            mock_session = {"user_id": 123, "user_name": "TestUser"}
            mock_get_session.return_value = mock_session
            
            await handle_help(message)
            
            # Проверяем что сессия была создана
            mock_get_session.assert_called_once_with(123, "TestUser")
            
            # Проверяем что сообщения были добавлены в историю
            assert mock_add_message.call_count == 2
            mock_add_message.assert_any_call(123, "user", "/help", 10)
            # Проверяем что ответ содержит примеры
            help_call = mock_add_message.call_args_list[1]
            assert "Примеры вопросов" in help_call[0][2]


class TestHandleMessage:
    """Тесты обработчика текстовых сообщений."""
    
    def create_mock_message(self, text="Test message", user_id=123, first_name="TestUser"):
        """Создание мок-объекта сообщения."""
        user = User(id=user_id, is_bot=False, first_name=first_name)
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
    async def test_handle_message_llm_not_initialized(self):
        """Тест обработки сообщения когда LLM не инициализирован."""
        message = self.create_mock_message("Test message")
        
        with patch('src.bot.handlers.llm_client', None), \
             patch('src.bot.handlers.system_prompt', None), \
             patch('src.bot.handlers.config', None):
            
            await handle_message(message)
            
            # Проверяем что было отправлено сообщение об ошибке
            message.answer.assert_called_once_with("Сервис временно недоступен. Попробуйте позже.")
    
    @pytest.mark.asyncio
    async def test_handle_message_too_long(self):
        """Тест обработки слишком длинного сообщения."""
        long_text = "x" * 1001  # Превышает лимит в 1000 символов
        message = self.create_mock_message(long_text)
        
        mock_config = MagicMock()
        mock_config.max_message_length = 1000
        
        with patch('src.bot.handlers.llm_client', MagicMock()), \
             patch('src.bot.handlers.system_prompt', "Test prompt"), \
             patch('src.bot.handlers.config', mock_config), \
             patch('src.bot.handlers.metrics_collector') as mock_metrics:
            
            await handle_message(message)
            
            # Проверяем что было отправлено сообщение об ошибке
            message.answer.assert_called_once_with("Сообщение слишком длинное. Максимум 1000 символов.")
            
            # Проверяем что метрика была записана
            mock_metrics.record_message.assert_called_once_with(123, 1001, False)
    
    @pytest.mark.asyncio
    async def test_handle_message_success(self):
        """Тест успешной обработки сообщения."""
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.max_message_length = 1000
        mock_config.max_history_size = 10
        mock_config.primary_model = "test-model"
        mock_config.fallback_model = "fallback-model"
        mock_config.retry_attempts = 3
        mock_config.temperature = 0.7
        mock_config.max_tokens = 1000
        mock_config.top_p = 0.9
        
        mock_llm_client = AsyncMock()
        mock_history = [{"role": "user", "content": "Previous message"}]
        
        with patch('src.bot.handlers.llm_client', mock_llm_client), \
             patch('src.bot.handlers.system_prompt', "Test prompt"), \
             patch('src.bot.handlers.config', mock_config), \
             patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.get_user_history', return_value=mock_history), \
             patch('src.bot.handlers.add_message') as mock_add_message, \
             patch('src.bot.handlers.generate_response_with_history') as mock_generate, \
             patch('src.bot.handlers.metrics_collector') as mock_metrics:
            
            mock_generate.return_value = "Test response"
            mock_session = {"user_id": 123, "user_name": "TestUser"}
            mock_get_session.return_value = mock_session
            
            await handle_message(message)
            
            # Проверяем что сессия была получена
            mock_get_session.assert_called_once_with(123, "TestUser")
            
            # Проверяем что история была получена
            from src.bot.handlers import get_user_history
            get_user_history.assert_called_once_with(123)
            
            # Проверяем что сообщения были добавлены в историю
            assert mock_add_message.call_count == 2
            mock_add_message.assert_any_call(123, "user", "Test message", 10)
            mock_add_message.assert_any_call(123, "assistant", "Test response", 10)
            
            # Проверяем что был вызван LLM
            mock_generate.assert_called_once()
            
            # Проверяем что метрика была записана
            mock_metrics.record_message.assert_called_once_with(123, 12, True)
    
    @pytest.mark.asyncio
    async def test_handle_message_llm_error(self):
        """Тест обработки ошибки LLM."""
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.max_message_length = 1000
        mock_config.max_history_size = 10
        
        mock_llm_client = AsyncMock()
        
        with patch('src.bot.handlers.llm_client', mock_llm_client), \
             patch('src.bot.handlers.system_prompt', "Test prompt"), \
             patch('src.bot.handlers.config', mock_config), \
             patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.get_user_history', return_value=[]), \
             patch('src.bot.handlers.add_message') as mock_add_message, \
             patch('src.bot.handlers.generate_response_with_history') as mock_generate, \
             patch('src.bot.handlers.metrics_collector') as mock_metrics, \
             patch('src.bot.handlers.LLMError') as mock_llm_error:
            
            mock_generate.side_effect = mock_llm_error("LLM failed")
            mock_session = {"user_id": 123, "user_name": "TestUser"}
            mock_get_session.return_value = mock_session
            
            await handle_message(message)
            
            # Проверяем что было отправлено сообщение об ошибке
            message.answer.assert_called_once_with("Извините, сервис временно недоступен. Попробуйте повторить запрос через несколько минут.")
            
            # Проверяем что метрика была записана
            mock_metrics.record_message.assert_called_once_with(123, 12, False)
    
    @pytest.mark.asyncio
    async def test_handle_message_unexpected_error(self):
        """Тест обработки неожиданной ошибки."""
        message = self.create_mock_message("Test message")
        
        mock_config = MagicMock()
        mock_config.max_message_length = 1000
        
        mock_llm_client = AsyncMock()
        
        with patch('src.bot.handlers.llm_client', mock_llm_client), \
             patch('src.bot.handlers.system_prompt', "Test prompt"), \
             patch('src.bot.handlers.config', mock_config), \
             patch('src.bot.handlers.get_user_session') as mock_get_session, \
             patch('src.bot.handlers.metrics_collector') as mock_metrics:
            
            mock_get_session.side_effect = Exception("Unexpected error")
            
            await handle_message(message)
            
            # Проверяем что было отправлено сообщение об ошибке
            message.answer.assert_called_once_with("Произошла внутренняя ошибка. Пожалуйста, попробуйте позже.")
            
            # Проверяем что метрика была записана
            mock_metrics.record_message.assert_called_once_with(123, 12, False)
