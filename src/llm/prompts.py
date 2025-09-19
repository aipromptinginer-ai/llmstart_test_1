"""Загрузка и управление системными промптами."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def load_system_prompt(prompt_path: str = "prompts/system_prompt.txt") -> str:
    """Загрузка системного промпта из файла."""
    try:
        prompt_file = Path(prompt_path)
        if not prompt_file.exists():
            raise FileNotFoundError(f"Файл промпта не найден: {prompt_path}")
        
        with open(prompt_file, 'r', encoding='utf-8') as f:
            prompt = f.read().strip()
        
        if not prompt:
            raise ValueError(f"Файл промпта пустой: {prompt_path}")
            
        logger.info(f"System prompt loaded from {prompt_path}, length: {len(prompt)}")
        return prompt
        
    except Exception as e:
        logger.error(f"Failed to load system prompt: {e}")
        # Fallback промпт согласно @vision.md 
        fallback_prompt = """Вы - ИИ-консультант по формулировке целей обучения согласно таксономии Блума.

Помогаете инструкторам и преподавателям составлять конкретные, измеримые цели обучения на основе 6 уровней когнитивного развития:

1. Знание (запоминание фактов)
2. Понимание (объяснение концепций)  
3. Применение (использование на практике)
4. Анализ (разбор на части)
5. Синтез (создание нового)
6. Оценка (критическое мышление)

Задавайте уточняющие вопросы о тематике, аудитории, уровне Блума и способах оценки. Предлагайте конкретные формулировки целей обучения."""
        
        logger.warning("Using fallback system prompt")
        return fallback_prompt
