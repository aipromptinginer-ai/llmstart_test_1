"""Система сбора и анализа метрик."""
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from dataclasses import dataclass, field
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class MessageMetrics:
    """Метрики сообщения."""
    user_id: int
    message_length: int
    timestamp: float
    processed: bool = True


@dataclass
class LLMMetrics:
    """Метрики LLM запроса."""
    success: bool
    model: str
    response_time: float
    timestamp: float
    error_type: str = ""


class MetricsCollector:
    """Сборщик метрик для мониторинга бота."""
    
    def __init__(self):
        self.message_metrics: List[MessageMetrics] = []
        self.llm_metrics: List[LLMMetrics] = []
        self.hourly_stats: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
            'messages_count': 0,
            'llm_requests': 0,
            'llm_success_rate': 0.0,
            'avg_response_time': 0.0,
            'total_tokens': 0,
            'errors_count': 0
        })
        self._cleanup_threshold_hours = 24  # Очистка метрик старше 24 часов
    
    def record_message(self, user_id: int, message_length: int, processed: bool = True) -> None:
        """Запись метрики сообщения."""
        metric = MessageMetrics(
            user_id=user_id,
            message_length=message_length,
            timestamp=time.time(),
            processed=processed
        )
        self.message_metrics.append(metric)
        
        # Обновление почасовой статистики
        hour_key = self._get_hour_key(metric.timestamp)
        self.hourly_stats[hour_key]['messages_count'] += 1
        
        logger.debug(f"Message metric recorded: user={user_id}, length={message_length}, processed={processed}")
    
    def record_llm_request(self, success: bool, model: str, response_time: float, error_type: str = "") -> None:
        """Запись метрики LLM запроса."""
        metric = LLMMetrics(
            success=success,
            model=model,
            response_time=response_time,
            timestamp=time.time(),
            error_type=error_type
        )
        self.llm_metrics.append(metric)
        
        # Обновление почасовой статистики
        hour_key = self._get_hour_key(metric.timestamp)
        stats = self.hourly_stats[hour_key]
        stats['llm_requests'] += 1
        
        if success:
            stats['llm_success_rate'] = self._calculate_success_rate(hour_key)
            stats['avg_response_time'] = self._calculate_avg_response_time(hour_key)
        else:
            stats['errors_count'] += 1
        
        logger.debug(f"LLM metric recorded: success={success}, model={model}, response_time={response_time:.2f}s")
    
    def get_hourly_stats(self) -> Dict[str, Dict[str, Any]]:
        """Получение почасовой статистики."""
        self._cleanup_old_metrics()
        return dict(self.hourly_stats)
    
    def get_current_hour_stats(self) -> Dict[str, Any]:
        """Получение статистики за текущий час."""
        current_hour = self._get_hour_key(time.time())
        return self.hourly_stats[current_hour].copy()
    
    def log_hourly_stats(self) -> None:
        """Логирование почасовой статистики."""
        current_stats = self.get_current_hour_stats()
        
        logger.info(f"=== Почасовая статистика ===")
        logger.info(f"Сообщений: {current_stats['messages_count']}")
        logger.info(f"LLM запросов: {current_stats['llm_requests']}")
        logger.info(f"Успешность LLM: {current_stats['llm_success_rate']:.1%}")
        logger.info(f"Среднее время ответа: {current_stats['avg_response_time']:.2f}s")
        logger.info(f"Ошибок: {current_stats['errors_count']}")
        logger.info(f"==========================")
    
    def _get_hour_key(self, timestamp: float) -> str:
        """Получение ключа часа для группировки метрик."""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:00")
    
    def _calculate_success_rate(self, hour_key: str) -> float:
        """Расчет процента успешных LLM запросов за час."""
        hour_metrics = [m for m in self.llm_metrics if self._get_hour_key(m.timestamp) == hour_key]
        if not hour_metrics:
            return 0.0
        
        successful = sum(1 for m in hour_metrics if m.success)
        return successful / len(hour_metrics)
    
    def _calculate_avg_response_time(self, hour_key: str) -> float:
        """Расчет среднего времени ответа LLM за час."""
        hour_metrics = [m for m in self.llm_metrics if self._get_hour_key(m.timestamp) == hour_key and m.success]
        if not hour_metrics:
            return 0.0
        
        return sum(m.response_time for m in hour_metrics) / len(hour_metrics)
    
    def _cleanup_old_metrics(self) -> None:
        """Очистка старых метрик для экономии памяти."""
        cutoff_time = time.time() - (self._cleanup_threshold_hours * 3600)
        
        # Очистка метрик сообщений
        self.message_metrics = [m for m in self.message_metrics if m.timestamp > cutoff_time]
        
        # Очистка метрик LLM
        self.llm_metrics = [m for m in self.llm_metrics if m.timestamp > cutoff_time]
        
        # Очистка почасовой статистики
        cutoff_hour = self._get_hour_key(cutoff_time)
        self.hourly_stats = {
            hour: stats for hour, stats in self.hourly_stats.items() 
            if hour >= cutoff_hour
        }
        
        logger.debug(f"Cleaned up metrics older than {self._cleanup_threshold_hours} hours")


# Глобальный экземпляр сборщика метрик
metrics_collector = MetricsCollector()
