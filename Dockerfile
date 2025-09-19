# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы конфигурации
COPY pyproject.toml ./

# Устанавливаем uv
RUN pip install uv

# Устанавливаем зависимости
RUN uv sync --frozen

# Копируем исходный код
COPY src/ ./src/
COPY prompts/ ./prompts/

# Создаем пользователя для безопасности
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app

# Устанавливаем переменные окружения
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Команда запуска
CMD ["uv", "run", "python", "src/main.py"]
