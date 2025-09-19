"""Тесты LLM клиента."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.llm.client import create_llm_client, generate_response_with_history, LLMError


class TestCreateLLMClient:
    """Тесты создания LLM клиента."""
    
    @pytest.mark.asyncio
    async def test_create_llm_client_success(self):
        """Тест успешного создания LLM клиента."""
        with patch('src.llm.client.AsyncOpenAI') as mock_openai:
            mock_client = AsyncMock()
            mock_openai.return_value = mock_client
            
            client = await create_llm_client("test_api_key")
            
            assert client == mock_client
            mock_openai.assert_called_once_with(
                api_key="test_api_key",
                base_url="https://openrouter.ai/api/v1"
            )
    
    @pytest.mark.asyncio
    async def test_create_llm_client_with_invalid_key(self):
        """Тест создания клиента с неверным ключом."""
        with patch('src.llm.client.AsyncOpenAI') as mock_openai:
            mock_openai.side_effect = Exception("Invalid API key")
            
            with pytest.raises(LLMError, match="Failed to create LLM client"):
                await create_llm_client("invalid_key")


class TestGenerateResponseWithHistory:
    """Тесты генерации ответов с историей."""
    
    @pytest.mark.asyncio
    async def test_generate_response_success(self):
        """Тест успешной генерации ответа."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
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
        mock_client.chat.completions.create.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_response_with_history(self):
        """Тест генерации ответа с историей сообщений."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response with history"
        mock_client.chat.completions.create.return_value = mock_response
        
        history = [
            {"role": "user", "content": "Previous message"},
            {"role": "assistant", "content": "Previous response"}
        ]
        
        response = await generate_response_with_history(
            client=mock_client,
            system_prompt="Test system prompt",
            user_message="Current message",
            message_history=history,
            primary_model="test-model",
            fallback_model="fallback-model",
            retry_attempts=3,
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )
        
        assert response == "Test response with history"
        
        # Проверяем что история была включена в запрос
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args[1]['messages']
        
        assert len(messages) == 4  # system + history + current user message
        assert messages[0]['role'] == 'system'
        assert messages[1]['role'] == 'user'
        assert messages[2]['role'] == 'assistant'
        assert messages[3]['role'] == 'user'
    
    @pytest.mark.asyncio
    async def test_generate_response_primary_model_failure_fallback_success(self):
        """Тест fallback на резервную модель при сбое основной."""
        mock_client = AsyncMock()
        
        # Первый вызов (основная модель) падает, второй (резервная) успешен
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Fallback response"
        
        mock_client.chat.completions.create.side_effect = [
            Exception("Primary model failed"),
            mock_response
        ]
        
        response = await generate_response_with_history(
            client=mock_client,
            system_prompt="Test system prompt",
            user_message="Test user message",
            message_history=[],
            primary_model="primary-model",
            fallback_model="fallback-model",
            retry_attempts=3,
            temperature=0.7,
            max_tokens=1000,
            top_p=0.9
        )
        
        assert response == "Fallback response"
        assert mock_client.chat.completions.create.call_count == 2
        
        # Проверяем что второй вызов использовал резервную модель
        second_call = mock_client.chat.completions.create.call_args_list[1]
        assert second_call[1]['model'] == "fallback-model"
    
    @pytest.mark.asyncio
    async def test_generate_response_all_models_fail(self):
        """Тест когда все модели падают."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = Exception("All models failed")
        
        with pytest.raises(LLMError, match="All models failed after 3 attempts"):
            await generate_response_with_history(
                client=mock_client,
                system_prompt="Test system prompt",
                user_message="Test user message",
                message_history=[],
                primary_model="primary-model",
                fallback_model="fallback-model",
                retry_attempts=3,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
    
    @pytest.mark.asyncio
    async def test_generate_response_retry_attempts(self):
        """Тест повторных попыток."""
        mock_client = AsyncMock()
        mock_client.chat.completions.create.side_effect = [
            Exception("Temporary failure 1"),
            Exception("Temporary failure 2"),
            Exception("Temporary failure 3")
        ]
        
        with pytest.raises(LLMError, match="All models failed after 3 attempts"):
            await generate_response_with_history(
                client=mock_client,
                system_prompt="Test system prompt",
                user_message="Test user message",
                message_history=[],
                primary_model="primary-model",
                fallback_model="fallback-model",
                retry_attempts=3,
                temperature=0.7,
                max_tokens=1000,
                top_p=0.9
            )
        
        # Проверяем что было сделано 3 попытки для каждой модели
        assert mock_client.chat.completions.create.call_count == 6  # 3 для primary + 3 для fallback
    
    @pytest.mark.asyncio
    async def test_generate_response_empty_response(self):
        """Тест обработки пустого ответа."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = ""  # Пустой ответ
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(LLMError, match="Empty response from LLM"):
            await generate_response_with_history(
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
    
    @pytest.mark.asyncio
    async def test_generate_response_no_choices(self):
        """Тест обработки ответа без choices."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.choices = []  # Пустой список choices
        mock_client.chat.completions.create.return_value = mock_response
        
        with pytest.raises(LLMError, match="No response choices from LLM"):
            await generate_response_with_history(
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
