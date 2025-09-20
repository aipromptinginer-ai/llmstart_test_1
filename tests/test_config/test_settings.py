"""Тесты конфигурации приложения."""
import pytest
import os
from unittest.mock import patch
from src.config.settings import Config, load_config, validate_config


class TestConfig:
    """Тесты класса Config."""
    
    def test_config_creation(self):
        """Тест создания конфигурации с валидными данными."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key"
        )
        
        assert config.telegram_bot_token == "test_token"
        assert config.openrouter_api_key == "test_key"
        assert config.primary_model == "qwen/qwen-2.5-72b-instruct:free"
        assert config.max_message_length == 1000
        assert config.enable_metrics is True
    
    def test_config_default_values(self):
        """Тест значений по умолчанию."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key"
        )
        
        assert config.temperature == 0.7
        assert config.max_tokens == 1500
        assert config.retry_attempts == 3
        assert config.memory_ttl_hours == 24
        assert config.max_history_size == 10
        assert config.cleanup_interval_hours == 6
        assert config.metrics_cleanup_hours == 24
        assert config.log_hourly_stats is True


class TestConfigValidation:
    """Тесты валидации конфигурации."""
    
    def test_valid_config_passes_validation(self):
        """Тест что валидная конфигурация проходит валидацию."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key"
        )
        
        # Не должно вызывать исключений
        validate_config(config)
    
    def test_missing_telegram_token_raises_error(self):
        """Тест что отсутствие токена Telegram вызывает ошибку."""
        config = Config(
            telegram_bot_token="",
            openrouter_api_key="test_key"
        )
        
        with pytest.raises(ValueError, match="TELEGRAM_BOT_TOKEN не установлен"):
            validate_config(config)
    
    def test_missing_openrouter_key_raises_error(self):
        """Тест что отсутствие ключа OpenRouter вызывает ошибку."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key=""
        )
        
        with pytest.raises(ValueError, match="OPENROUTER_API_KEY не установлен"):
            validate_config(config)
    
    def test_invalid_temperature_raises_error(self):
        """Тест что неверная температура вызывает ошибку."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            temperature=3.0  # Вне допустимого диапазона
        )
        
        with pytest.raises(ValueError, match="TEMPERATURE должна быть от 0.0 до 2.0"):
            validate_config(config)
    
    def test_invalid_max_tokens_raises_error(self):
        """Тест что неверное количество токенов вызывает ошибку."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            max_tokens=0  # Должно быть > 0
        )
        
        with pytest.raises(ValueError, match="MAX_TOKENS должен быть > 0"):
            validate_config(config)
    
    def test_invalid_top_p_raises_error(self):
        """Тест что неверный top_p вызывает ошибку."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            top_p=1.5  # Вне допустимого диапазона
        )
        
        with pytest.raises(ValueError, match="TOP_P должен быть от 0.0 до 1.0"):
            validate_config(config)
    
    def test_invalid_message_length_raises_error(self):
        """Тест что неверная длина сообщения вызывает ошибку."""
        config = Config(
            telegram_bot_token="test_token",
            openrouter_api_key="test_key",
            max_message_length=0  # Должно быть > 0
        )
        
        with pytest.raises(ValueError, match="MAX_MESSAGE_LENGTH должен быть > 0"):
            validate_config(config)


class TestLoadConfig:
    """Тесты загрузки конфигурации."""
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'env_test_token',
        'OPENROUTER_API_KEY': 'env_test_key',
        'PRIMARY_MODEL': 'env_test_model',
        'TEMPERATURE': '0.8',
        'MAX_MESSAGE_LENGTH': '2000'
    })
    def test_load_config_from_env(self):
        """Тест загрузки конфигурации из переменных окружения."""
        config = load_config()
        
        assert config.telegram_bot_token == 'env_test_token'
        assert config.openrouter_api_key == 'env_test_key'
        assert config.primary_model == 'env_test_model'
        assert config.temperature == 0.8
        assert config.max_message_length == 2000
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'env_test_token',
        'OPENROUTER_API_KEY': 'env_test_key',
        'ENABLE_METRICS': 'false',
        'LOG_HOURLY_STATS': 'false'
    })
    def test_load_config_boolean_values(self):
        """Тест загрузки булевых значений из переменных окружения."""
        config = load_config()
        
        assert config.enable_metrics is False
        assert config.log_hourly_stats is False
    
    @patch.dict(os.environ, {
        'TELEGRAM_BOT_TOKEN': 'env_test_token',
        'OPENROUTER_API_KEY': 'env_test_key'
    })
    def test_load_config_uses_defaults(self):
        """Тест что используются значения по умолчанию для неопределенных переменных."""
        config = load_config()
        
        assert config.primary_model == "qwen/qwen-2.5-72b-instruct:free"
        assert config.temperature == 0.7
        assert config.max_tokens == 1500
        assert config.enable_metrics is True
