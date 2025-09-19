"""Тесты системы памяти диалогов."""
import pytest
import time
from unittest.mock import patch
from src.memory.storage import (
    get_user_session, 
    add_message, 
    get_user_history, 
    start_cleanup_task,
    user_sessions
)


class TestUserSessions:
    """Тесты управления сессиями пользователей."""
    
    def setup_method(self):
        """Очистка состояния перед каждым тестом."""
        user_sessions.clear()
    
    def test_get_user_session_new_user(self):
        """Тест создания новой сессии пользователя."""
        session = get_user_session(123, "TestUser")
        
        assert session['user_id'] == 123
        assert session['user_name'] == "TestUser"
        assert 'created_at' in session
        assert 'last_activity' in session
        assert session['messages'] == []
    
    def test_get_user_session_existing_user(self):
        """Тест получения существующей сессии пользователя."""
        # Создаем сессию
        session1 = get_user_session(123, "TestUser")
        session1['messages'] = [{"role": "user", "content": "test"}]
        
        # Получаем ту же сессию
        session2 = get_user_session(123, "TestUser")
        
        assert session1 is session2
        assert session2['messages'] == [{"role": "user", "content": "test"}]
    
    def test_get_user_session_multiple_users(self):
        """Тест работы с несколькими пользователями."""
        session1 = get_user_session(123, "User1")
        session2 = get_user_session(456, "User2")
        
        assert session1['user_id'] == 123
        assert session2['user_id'] == 456
        assert session1 is not session2
        assert len(user_sessions) == 2


class TestMessageStorage:
    """Тесты хранения сообщений."""
    
    def setup_method(self):
        """Очистка состояния перед каждым тестом."""
        user_sessions.clear()
    
    def test_add_message_new_user(self):
        """Тест добавления сообщения для нового пользователя."""
        add_message(123, "user", "Hello", 10)
        
        session = user_sessions[123]
        assert len(session['messages']) == 1
        assert session['messages'][0]['role'] == "user"
        assert session['messages'][0]['content'] == "Hello"
        assert 'timestamp' in session['messages'][0]
    
    def test_add_message_existing_user(self):
        """Тест добавления сообщения для существующего пользователя."""
        # Создаем сессию
        get_user_session(123, "TestUser")
        
        # Добавляем сообщения
        add_message(123, "user", "Hello", 10)
        add_message(123, "assistant", "Hi there!", 10)
        
        session = user_sessions[123]
        assert len(session['messages']) == 2
        assert session['messages'][0]['role'] == "user"
        assert session['messages'][1]['role'] == "assistant"
    
    def test_add_message_max_history_size(self):
        """Тест ограничения размера истории."""
        get_user_session(123, "TestUser")
        
        # Добавляем больше сообщений чем лимит
        for i in range(15):  # Лимит 10
            add_message(123, "user", f"Message {i}", 10)
        
        session = user_sessions[123]
        assert len(session['messages']) == 10  # Должно быть ограничено
        assert session['messages'][0]['content'] == "Message 5"  # Первые 5 удалены
        assert session['messages'][-1]['content'] == "Message 14"  # Последние 10 сохранены
    
    def test_add_message_updates_last_activity(self):
        """Тест обновления времени последней активности."""
        session = get_user_session(123, "TestUser")
        original_time = session['last_activity']
        
        time.sleep(0.01)  # Небольшая задержка
        add_message(123, "user", "Hello", 10)
        
        assert session['last_activity'] > original_time


class TestUserHistory:
    """Тесты получения истории пользователя."""
    
    def setup_method(self):
        """Очистка состояния перед каждым тестом."""
        user_sessions.clear()
    
    def test_get_user_history_empty(self):
        """Тест получения пустой истории."""
        history = get_user_history(123)
        assert history == []
    
    def test_get_user_history_with_messages(self):
        """Тест получения истории с сообщениями."""
        get_user_session(123, "TestUser")
        
        add_message(123, "user", "Hello", 10)
        add_message(123, "assistant", "Hi!", 10)
        add_message(123, "user", "How are you?", 10)
        
        history = get_user_history(123)
        
        assert len(history) == 3
        assert history[0]['role'] == "user"
        assert history[0]['content'] == "Hello"
        assert history[1]['role'] == "assistant"
        assert history[1]['content'] == "Hi!"
        assert history[2]['role'] == "user"
        assert history[2]['content'] == "How are you?"
    
    def test_get_user_history_nonexistent_user(self):
        """Тест получения истории для несуществующего пользователя."""
        history = get_user_history(999)
        assert history == []


class TestCleanupTask:
    """Тесты задачи очистки."""
    
    def setup_method(self):
        """Очистка состояния перед каждым тестом."""
        user_sessions.clear()
    
    @pytest.mark.asyncio
    async def test_start_cleanup_task(self):
        """Тест запуска задачи очистки."""
        # Создаем старую сессию
        session = get_user_session(123, "TestUser")
        old_time = time.time() - 3600  # 1 час назад
        session['last_activity'] = old_time
        
        # Запускаем задачу очистки с коротким интервалом
        task = await start_cleanup_task(cleanup_interval_hours=0.001, ttl_hours=0.5)
        
        # Ждем выполнения
        await asyncio.sleep(0.1)
        
        # Проверяем что сессия была удалена
        assert 123 not in user_sessions
        
        # Останавливаем задачу
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_cleanup_task_preserves_active_sessions(self):
        """Тест что задача очистки сохраняет активные сессии."""
        # Создаем активную сессию
        session = get_user_session(123, "TestUser")
        session['last_activity'] = time.time()  # Сейчас
        
        # Создаем старую сессию
        old_session = get_user_session(456, "OldUser")
        old_session['last_activity'] = time.time() - 3600  # 1 час назад
        
        # Запускаем задачу очистки
        task = await start_cleanup_task(cleanup_interval_hours=0.001, ttl_hours=0.5)
        
        # Ждем выполнения
        await asyncio.sleep(0.1)
        
        # Проверяем что активная сессия сохранена, а старая удалена
        assert 123 in user_sessions
        assert 456 not in user_sessions
        
        # Останавливаем задачу
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass
    
    @pytest.mark.asyncio
    async def test_cleanup_task_single_instance(self):
        """Тест что задача очистки запускается."""
        # Запускаем задачу
        task = await start_cleanup_task(cleanup_interval_hours=1, ttl_hours=24)
        
        # Проверяем что задача создана
        assert task is not None
        
        # Останавливаем задачу
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


class TestMessageFormat:
    """Тесты формата сообщений."""
    
    def setup_method(self):
        """Очистка состояния перед каждым тестом."""
        user_sessions.clear()
    
    def test_message_format_structure(self):
        """Тест структуры сообщения."""
        get_user_session(123, "TestUser")
        add_message(123, "user", "Test message", 10)
        
        session = user_sessions[123]
        message = session['messages'][0]
        
        assert 'role' in message
        assert 'content' in message
        assert 'timestamp' in message
        assert message['role'] == "user"
        assert message['content'] == "Test message"
        assert isinstance(message['timestamp'], float)
    
    def test_message_timestamp_ordering(self):
        """Тест упорядочивания сообщений по времени."""
        get_user_session(123, "TestUser")
        
        add_message(123, "user", "First", 10)
        time.sleep(0.01)
        add_message(123, "assistant", "Second", 10)
        time.sleep(0.01)
        add_message(123, "user", "Third", 10)
        
        session = user_sessions[123]
        messages = session['messages']
        
        # Проверяем что сообщения упорядочены по времени
        for i in range(len(messages) - 1):
            assert messages[i]['timestamp'] <= messages[i + 1]['timestamp']
