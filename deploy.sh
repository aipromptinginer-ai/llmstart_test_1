#!/bin/bash

# Скрипт для деплоя бота на Railway
# Использование: ./deploy.sh

set -e

echo "🚀 Деплой LLM-ассистента на Railway"
echo "=================================="

# Проверка наличия git репозитория
if [ ! -d ".git" ]; then
    echo "❌ Ошибка: Не найден git репозиторий"
    echo "Сначала выполните: git init && git add . && git commit -m 'Initial commit'"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    echo "⚠️  Предупреждение: Файл .env не найден"
    echo "Создайте .env файл с переменными:"
    echo "TELEGRAM_BOT_TOKEN=ваш_токен"
    echo "OPENROUTER_API_KEY=ваш_ключ"
    echo ""
    read -p "Продолжить без .env? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Проверка Railway CLI
if ! command -v railway &> /dev/null; then
    echo "📦 Установка Railway CLI..."
    curl -fsSL https://railway.app/install.sh | sh
    echo "✅ Railway CLI установлен"
else
    echo "✅ Railway CLI уже установлен"
fi

# Логин в Railway
echo "🔐 Вход в Railway..."
railway login

# Создание проекта
echo "🏗️  Создание проекта на Railway..."
railway init

# Настройка переменных окружения
echo "⚙️  Настройка переменных окружения..."

if [ -f ".env" ]; then
    echo "📋 Загрузка переменных из .env файла..."
    railway variables --file .env
else
    echo "📝 Настройка переменных вручную..."
    echo "Введите значения переменных:"
    
    read -p "TELEGRAM_BOT_TOKEN: " TELEGRAM_BOT_TOKEN
    read -p "OPENROUTER_API_KEY: " OPENROUTER_API_KEY
    
    railway variables set TELEGRAM_BOT_TOKEN="$TELEGRAM_BOT_TOKEN"
    railway variables set OPENROUTER_API_KEY="$OPENROUTER_API_KEY"
    
    # Опциональные переменные
    railway variables set PRIMARY_MODEL="qwen/qwen-2.5-72b-instruct:free"
    railway variables set FALLBACK_MODEL="deepseek/deepseek-chat-v3.1:free"
    railway variables set TEMPERATURE="0.7"
    railway variables set MAX_TOKENS="1500"
    railway variables set MAX_MESSAGE_LENGTH="1000"
    railway variables set ENABLE_METRICS="true"
    railway variables set LOG_HOURLY_STATS="true"
fi

# Деплой
echo "🚀 Запуск деплоя..."
railway up

# Получение URL
echo "🔗 Получение URL приложения..."
URL=$(railway domain)
echo "✅ Бот развернут по адресу: $URL"

echo ""
echo "🎉 Деплой завершен!"
echo "📊 Мониторинг: https://railway.app/dashboard"
echo "📖 Логи: railway logs"
echo "🛑 Остановка: railway down"
echo ""
echo "💡 Полезные команды:"
echo "  railway status    - статус приложения"
echo "  railway logs      - просмотр логов"
echo "  railway shell     - подключение к контейнеру"
echo "  railway down      - остановка приложения"
