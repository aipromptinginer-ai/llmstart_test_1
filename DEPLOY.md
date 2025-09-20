# 🚀 Инструкция по деплою на Railway

## 📋 Подготовка к деплою

### 1. Создание аккаунта Railway

1. Перейдите на [railway.app](https://railway.app)
2. Нажмите **"Sign Up"**
3. Выберите **"Sign in with GitHub"** (рекомендуется)
4. Авторизуйтесь через GitHub
5. Подтвердите email адрес

### 2. Подготовка репозитория

Убедитесь, что ваш код загружен в GitHub:

```bash
# Если еще не создан репозиторий на GitHub
git remote add origin https://github.com/ваш-username/llm-learning-goals-bot.git
git push -u origin main

# Или если репозиторий уже существует
git push origin main
```

## 🚀 Деплой на Railway

### Шаг 1: Создание проекта

1. Войдите в [Railway Dashboard](https://railway.app/dashboard)
2. Нажмите **"New Project"**
3. Выберите **"Deploy from GitHub repo"**
4. Найдите ваш репозиторий `llm-learning-goals-bot`
5. Нажмите **"Deploy Now"**

### Шаг 2: Настройка переменных окружения

В Railway Dashboard:

1. Откройте ваш проект
2. Перейдите на вкладку **"Variables"**
3. Добавьте следующие переменные:

```bash
# Обязательные переменные
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENROUTER_API_KEY=ваш_openrouter_api_key

# Опциональные (можно оставить по умолчанию)
PRIMARY_MODEL=qwen/qwen-2.5-72b-instruct:free
FALLBACK_MODEL=deepseek/deepseek-chat-v3.1:free
TEMPERATURE=0.7
MAX_TOKENS=1500
TOP_P=0.9
RETRY_ATTEMPTS=3
MAX_MESSAGE_LENGTH=1000
MEMORY_TTL_HOURS=24
MAX_HISTORY_SIZE=10
CLEANUP_INTERVAL_HOURS=6
ENABLE_METRICS=true
METRICS_CLEANUP_HOURS=24
LOG_HOURLY_STATS=true
```

### Шаг 3: Настройка сборки

Railway автоматически определит настройки из `railway.json`, но можно проверить:

1. Перейдите на вкладку **"Settings"**
2. В разделе **"Build & Deploy"**:
   - **Build Command**: `uv sync`
   - **Start Command**: `uv run python src/main.py`
   - **Dockerfile Path**: `Dockerfile`

### Шаг 4: Получение токенов

#### Telegram Bot Token:
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен

#### OpenRouter API Key:
1. Перейдите на [openrouter.ai](https://openrouter.ai)
2. Зарегистрируйтесь или войдите
3. Перейдите в **"Keys"** в личном кабинете
4. Создайте новый API ключ
5. Скопируйте ключ

## 🔧 Локальная настройка для тестирования

### Создание .env файла

```bash
# Создайте .env файл в корне проекта
cp .env.example .env

# Отредактируйте .env файл
nano .env
```

Содержимое `.env`:
```bash
TELEGRAM_BOT_TOKEN=ваш_telegram_bot_token
OPENROUTER_API_KEY=ваш_openrouter_api_key
```

### Тестирование локально

```bash
# Установка зависимостей
make install

# Запуск бота
make run

# Или через Docker
make docker-compose-up
```

## 📊 Мониторинг и логи

### Railway Dashboard

1. **Logs**: Просмотр логов в реальном времени
2. **Metrics**: Мониторинг использования ресурсов
3. **Deployments**: История деплоев

### Логи бота

Бот автоматически логирует:
- Статистику по часам
- Ошибки и предупреждения
- Метрики использования

## 🛠️ Обновление бота

### Автоматический деплой

Railway автоматически деплоит при push в main ветку:

```bash
git add .
git commit -m "Обновление бота"
git push origin main
```

### Ручной деплой

1. В Railway Dashboard нажмите **"Deploy"**
2. Выберите коммит для деплоя
3. Дождитесь завершения сборки

## 🔍 Отладка проблем

### Частые проблемы

1. **Бот не отвечает**:
   - Проверьте правильность `TELEGRAM_BOT_TOKEN`
   - Убедитесь что бот не заблокирован

2. **Ошибки LLM**:
   - Проверьте `OPENROUTER_API_KEY`
   - Убедитесь что на счету есть средства

3. **Ошибки сборки**:
   - Проверьте логи в Railway Dashboard
   - Убедитесь что все зависимости указаны в `pyproject.toml`

### Просмотр логов

```bash
# В Railway Dashboard
# Перейдите в раздел "Deployments" -> выберите деплой -> "View Logs"
```

## 📈 Масштабирование

### Railway планы

- **Hobby** (бесплатно): 500 часов в месяц
- **Pro** ($5/месяц): неограниченное время
- **Team**: для команд

### Рекомендации

1. Начните с Hobby плана
2. Мониторьте использование через логи
3. При необходимости переходите на Pro

## 🎯 Готово!

После выполнения всех шагов ваш бот будет доступен 24/7 на Railway!

**Полезные ссылки:**
- [Railway Dashboard](https://railway.app/dashboard)
- [Railway Documentation](https://docs.railway.app)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenRouter API](https://openrouter.ai/docs)
