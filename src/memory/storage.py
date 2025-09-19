"""Хранение и управление историей диалогов."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, TypedDict
import asyncio

logger = logging.getLogger(__name__)


class Message(TypedDict):
    """Структура сообщения в истории."""
    role: str          # "user" или "assistant"
    content: str       # Текст сообщения
    timestamp: datetime


class UserSession(TypedDict):
    """Структура сессии пользователя."""
    user_id: int
    user_name: str
    history: List[Message]
    last_activity: datetime
    created_at: datetime


# Глобальное хранилище сессий пользователей
user_sessions: Dict[int, UserSession] = {}


def get_user_session(user_id: int, user_name: str) -> UserSession:
    """Получение или создание сессии пользователя."""
    if user_id not in user_sessions:
        logger.info(f"Creating new session for user {user_id}")
        user_sessions[user_id] = UserSession(
            user_id=user_id,
            user_name=user_name,
            history=[],
            last_activity=datetime.now(),
            created_at=datetime.now()
        )
    else:
        # Обновление времени активности и имени
        user_sessions[user_id]["last_activity"] = datetime.now()
        user_sessions[user_id]["user_name"] = user_name
        
    return user_sessions[user_id]


def add_message(user_id: int, role: str, content: str, max_history_size: int = 10) -> None:
    """Добавление сообщения в историю пользователя."""
    if user_id not in user_sessions:
        logger.warning(f"Session not found for user {user_id}")
        return
    
    message = Message(
        role=role,
        content=content,
        timestamp=datetime.now()
    )
    
    session = user_sessions[user_id]
    session["history"].append(message)
    session["last_activity"] = datetime.now()
    
    # Ограничение размера истории
    if len(session["history"]) > max_history_size:
        removed_count = len(session["history"]) - max_history_size
        session["history"] = session["history"][-max_history_size:]
        logger.debug(f"Trimmed {removed_count} old messages for user {user_id}")
    
    logger.debug(f"Added {role} message for user {user_id}, history size: {len(session['history'])}")


def get_user_history(user_id: int) -> List[Dict[str, str]]:
    """Получение истории пользователя в формате OpenAI."""
    if user_id not in user_sessions:
        return []
    
    history = []
    for msg in user_sessions[user_id]["history"]:
        history.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    logger.debug(f"Retrieved history for user {user_id}: {len(history)} messages")
    return history


def cleanup_old_sessions(ttl_hours: int = 24) -> int:
    """Очистка неактивных сессий."""
    cutoff_time = datetime.now() - timedelta(hours=ttl_hours)
    old_sessions = []
    
    for user_id, session in user_sessions.items():
        if session["last_activity"] < cutoff_time:
            old_sessions.append(user_id)
    
    for user_id in old_sessions:
        del user_sessions[user_id]
        logger.info(f"Cleaned up old session for user {user_id}")
    
    logger.info(f"Cleanup completed: removed {len(old_sessions)} sessions, {len(user_sessions)} active")
    return len(old_sessions)


async def start_cleanup_task(cleanup_interval_hours: int = 6, ttl_hours: int = 24):
    """Запуск фоновой задачи очистки."""
    logger.info(f"Starting cleanup task: every {cleanup_interval_hours}h, TTL {ttl_hours}h")
    
    while True:
        try:
            await asyncio.sleep(cleanup_interval_hours * 3600)  # часы в секунды
            cleanup_old_sessions(ttl_hours)
        except Exception as e:
            logger.error(f"Cleanup task error: {e}")


def clear_user_history(user_id: int) -> None:
    """Очистка истории диалога пользователя."""
    if user_id in user_sessions:
        user_sessions[user_id]["history"] = []
        user_sessions[user_id]["last_activity"] = datetime.now()
        logger.info(f"Cleared history for user {user_id}")
    else:
        logger.warning(f"Session not found for user {user_id} during clear")


def get_session_stats() -> Dict[str, int]:
    """Статистика сессий для мониторинга."""
    return {
        "total_sessions": len(user_sessions),
        "active_users": len([s for s in user_sessions.values() 
                           if s["last_activity"] > datetime.now() - timedelta(hours=1)])
    }
