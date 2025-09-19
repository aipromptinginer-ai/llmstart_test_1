"""Интеграционные тесты бота с реальными API."""
import asyncio
import os
import sys
import logging
from unittest.mock import patch

# Добавляем src в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from config.settings import load_config
from bot.handlers import init_llm
from monitoring.metrics import metrics_collector


async def test_config_loading():
    """Тест загрузки конфигурации."""
    print("🔧 Тестирование загрузки конфигурации...")
    
    try:
        config = load_config()
        print(f"✅ Конфигурация загружена успешно")
        print(f"   - Primary model: {config.primary_model}")
        print(f"   - Max message length: {config.max_message_length}")
        print(f"   - Enable metrics: {config.enable_metrics}")
        return True
    except Exception as e:
        print(f"❌ Ошибка загрузки конфигурации: {e}")
        return False


async def test_llm_initialization():
    """Тест инициализации LLM."""
    print("🤖 Тестирование инициализации LLM...")
    
    try:
        config = load_config()
        
        # Проверяем наличие API ключей
        if not config.telegram_bot_token:
            print("⚠️  TELEGRAM_BOT_TOKEN не установлен, пропускаем тест")
            return True
            
        if not config.openrouter_api_key:
            print("⚠️  OPENROUTER_API_KEY не установлен, пропускаем тест")
            return True
        
        # Инициализируем LLM
        await init_llm(config)
        print("✅ LLM инициализирован успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации LLM: {e}")
        return False


async def test_metrics_system():
    """Тест системы метрик."""
    print("📊 Тестирование системы метрик...")
    
    try:
        # Очищаем метрики
        metrics_collector.message_metrics.clear()
        metrics_collector.llm_metrics.clear()
        metrics_collector.hourly_stats.clear()
        
        # Записываем тестовые метрики
        metrics_collector.record_message(123, 100, True)
        metrics_collector.record_message(124, 200, False)
        metrics_collector.record_llm_request(True, "test-model", 1.5)
        metrics_collector.record_llm_request(False, "test-model", 0.5, "TestError")
        
        # Проверяем статистику
        stats = metrics_collector.get_current_hour_stats()
        
        assert stats['messages_count'] == 2
        assert stats['llm_requests'] == 2
        assert stats['llm_success_rate'] == 0.5
        assert stats['errors_count'] == 1
        
        print("✅ Система метрик работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в системе метрик: {e}")
        return False


async def test_memory_system():
    """Тест системы памяти."""
    print("🧠 Тестирование системы памяти...")
    
    try:
        from memory.storage import get_user_session, add_message, get_user_history
        
        # Очищаем память
        from memory.storage import user_sessions
        user_sessions.clear()
        
        # Создаем сессию пользователя
        session = get_user_session(123, "TestUser")
        assert session['user_id'] == 123
        assert session['user_name'] == "TestUser"
        
        # Добавляем сообщения
        add_message(123, "user", "Hello", 10)
        add_message(123, "assistant", "Hi there!", 10)
        
        # Получаем историю
        history = get_user_history(123)
        assert len(history) == 2
        assert history[0]['role'] == "user"
        assert history[1]['role'] == "assistant"
        
        print("✅ Система памяти работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в системе памяти: {e}")
        return False


async def test_llm_client_mock():
    """Тест LLM клиента с моком."""
    print("🔮 Тестирование LLM клиента (мок)...")
    
    try:
        from llm.client import create_llm_client, generate_response_with_history
        from unittest.mock import AsyncMock, MagicMock
        
        # Создаем мок клиента
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Тестируем генерацию ответа
        response = await generate_response_with_history(
            client=mock_client,
            system_prompt="Test system prompt",
            user_message="Test user message",
            message_history=[],
            primary_model="test-model",
            fallback_model="fallback-model",
            retry_attempts=3,
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )
        
        assert response == "Test response"
        print("✅ LLM клиент работает корректно (мок)")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка в LLM клиенте: {e}")
        return False


async def run_integration_tests():
    """Запуск всех интеграционных тестов."""
    print("🚀 Запуск интеграционных тестов...")
    print("=" * 50)
    
    tests = [
        test_config_loading,
        test_metrics_system,
        test_memory_system,
        test_llm_client_mock,
        test_llm_initialization,  # Последний, так как может требовать реальные API ключи
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            result = await test()
            if result:
                passed += 1
        except Exception as e:
            print(f"❌ Неожиданная ошибка в тесте {test.__name__}: {e}")
        
        print()  # Пустая строка между тестами
    
    print("=" * 50)
    print(f"📈 Результаты: {passed}/{total} тестов прошли успешно")
    
    if passed == total:
        print("🎉 Все интеграционные тесты прошли успешно!")
        return True
    else:
        print("⚠️  Некоторые тесты не прошли. Проверьте конфигурацию.")
        return False


if __name__ == "__main__":
    asyncio.run(run_integration_tests())
