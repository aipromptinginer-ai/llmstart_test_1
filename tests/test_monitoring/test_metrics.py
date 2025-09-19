"""Тесты системы мониторинга и метрик."""
import pytest
import time
from datetime import datetime
from src.monitoring.metrics import MetricsCollector, MessageMetrics, LLMMetrics


class TestMessageMetrics:
    """Тесты метрик сообщений."""
    
    def test_message_metrics_creation(self):
        """Тест создания метрики сообщения."""
        timestamp = time.time()
        metric = MessageMetrics(
            user_id=123,
            message_length=100,
            timestamp=timestamp,
            processed=True
        )
        
        assert metric.user_id == 123
        assert metric.message_length == 100
        assert metric.timestamp == timestamp
        assert metric.processed is True


class TestLLMMetrics:
    """Тесты метрик LLM."""
    
    def test_llm_metrics_creation(self):
        """Тест создания метрики LLM."""
        timestamp = time.time()
        metric = LLMMetrics(
            success=True,
            model="test-model",
            response_time=1.5,
            timestamp=timestamp,
            error_type=""
        )
        
        assert metric.success is True
        assert metric.model == "test-model"
        assert metric.response_time == 1.5
        assert metric.timestamp == timestamp
        assert metric.error_type == ""


class TestMetricsCollector:
    """Тесты сборщика метрик."""
    
    def setup_method(self):
        """Настройка перед каждым тестом."""
        self.collector = MetricsCollector()
    
    def test_record_message(self):
        """Тест записи метрики сообщения."""
        self.collector.record_message(123, 100, True)
        
        assert len(self.collector.message_metrics) == 1
        metric = self.collector.message_metrics[0]
        assert metric.user_id == 123
        assert metric.message_length == 100
        assert metric.processed is True
    
    def test_record_llm_request(self):
        """Тест записи метрики LLM запроса."""
        self.collector.record_llm_request(True, "test-model", 1.5)
        
        assert len(self.collector.llm_metrics) == 1
        metric = self.collector.llm_metrics[0]
        assert metric.success is True
        assert metric.model == "test-model"
        assert metric.response_time == 1.5
    
    def test_record_multiple_messages(self):
        """Тест записи нескольких сообщений."""
        self.collector.record_message(123, 100, True)
        self.collector.record_message(124, 200, False)
        self.collector.record_message(125, 150, True)
        
        assert len(self.collector.message_metrics) == 3
        assert self.collector.hourly_stats[self.collector._get_hour_key(time.time())]['messages_count'] == 3
    
    def test_record_multiple_llm_requests(self):
        """Тест записи нескольких LLM запросов."""
        self.collector.record_llm_request(True, "model1", 1.0)
        self.collector.record_llm_request(False, "model2", 0.5, "TestError")
        self.collector.record_llm_request(True, "model1", 2.0)
        
        assert len(self.collector.llm_metrics) == 3
        stats = self.collector.hourly_stats[self.collector._get_hour_key(time.time())]
        assert stats['llm_requests'] == 3
        assert stats['errors_count'] == 1
    
    def test_get_current_hour_stats(self):
        """Тест получения статистики за текущий час."""
        # Записываем тестовые данные
        self.collector.record_message(123, 100, True)
        self.collector.record_message(124, 200, False)
        self.collector.record_llm_request(True, "test-model", 1.5)
        self.collector.record_llm_request(False, "test-model", 0.5, "TestError")
        
        stats = self.collector.get_current_hour_stats()
        
        assert stats['messages_count'] == 2
        assert stats['llm_requests'] == 2
        assert stats['llm_success_rate'] == 0.5  # 1 из 2 успешных
        assert stats['avg_response_time'] == 1.5  # Только успешные запросы
        assert stats['errors_count'] == 1
    
    def test_calculate_success_rate(self):
        """Тест расчета процента успешных запросов."""
        # Добавляем метрики с разными результатами
        self.collector.record_llm_request(True, "model1", 1.0)
        self.collector.record_llm_request(False, "model1", 0.5, "Error1")
        self.collector.record_llm_request(True, "model1", 2.0)
        
        current_hour = self.collector._get_hour_key(time.time())
        success_rate = self.collector._calculate_success_rate(current_hour)
        
        assert success_rate == 2/3  # 2 успешных из 3
    
    def test_calculate_avg_response_time(self):
        """Тест расчета среднего времени ответа."""
        # Добавляем только успешные запросы
        self.collector.record_llm_request(True, "model1", 1.0)
        self.collector.record_llm_request(True, "model1", 2.0)
        self.collector.record_llm_request(True, "model1", 3.0)
        
        current_hour = self.collector._get_hour_key(time.time())
        avg_time = self.collector._calculate_avg_response_time(current_hour)
        
        assert avg_time == 2.0  # (1.0 + 2.0 + 3.0) / 3
    
    def test_get_hour_key(self):
        """Тест получения ключа часа."""
        timestamp = time.time()
        hour_key = self.collector._get_hour_key(timestamp)
        
        # Проверяем формат: YYYY-MM-DD HH:00
        assert len(hour_key) == 16
        assert hour_key.count(':') == 2
        assert hour_key.count('-') == 2
        assert hour_key.endswith(':00')
    
    def test_cleanup_old_metrics(self):
        """Тест очистки старых метрик."""
        # Устанавливаем короткий порог очистки для теста
        self.collector._cleanup_threshold_hours = 0.001  # ~3.6 секунды
        
        # Добавляем старые метрики
        old_timestamp = time.time() - 10  # 10 секунд назад
        self.collector.message_metrics.append(
            MessageMetrics(123, 100, old_timestamp, True)
        )
        self.collector.llm_metrics.append(
            LLMMetrics(True, "test", 1.0, old_timestamp, "")
        )
        
        # Добавляем новые метрики
        self.collector.record_message(124, 200, True)
        self.collector.record_llm_request(True, "test", 1.5)
        
        # Очищаем старые метрики
        self.collector._cleanup_old_metrics()
        
        # Должны остаться только новые метрики
        assert len(self.collector.message_metrics) == 1
        assert len(self.collector.llm_metrics) == 1
        assert self.collector.message_metrics[0].user_id == 124
        assert self.collector.llm_metrics[0].response_time == 1.5
    
    def test_log_hourly_stats(self, caplog):
        """Тест логирования почасовой статистики."""
        # Добавляем тестовые данные
        self.collector.record_message(123, 100, True)
        self.collector.record_llm_request(True, "test-model", 1.5)
        
        # Логируем статистику
        self.collector.log_hourly_stats()
        
        # Проверяем что в логах есть нужная информация
        log_messages = [record.message for record in caplog.records]
        assert any("Почасовая статистика" in msg for msg in log_messages)
        assert any("Сообщений: 1" in msg for msg in log_messages)
        assert any("LLM запросов: 1" in msg for msg in log_messages)
