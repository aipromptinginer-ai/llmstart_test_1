FROM python:3.11-slim

WORKDIR /app

# Копируем файлы проекта
COPY . .

# Устанавливаем uv
RUN pip install uv

# Синхронизируем зависимости
RUN uv sync

# Запускаем приложение
CMD ["uv", "run", "python", "src/main.py"]
