# ⚡ Быстрый старт

## 🚀 Деплой на Railway за 5 минут

### 1. Создайте аккаунт Railway
- Перейдите на [railway.app](https://railway.app)
- Войдите через GitHub

### 2. Получите токены

#### Telegram Bot:
1. Найдите [@BotFather](https://t.me/botfather) в Telegram
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте токен

#### OpenRouter API:
1. Зайдите на [openrouter.ai](https://openrouter.ai)
2. Создайте аккаунт
3. Перейдите в "Keys" → "Create Key"
4. Скопируйте ключ

### 3. Деплой

#### Вариант A: Через Railway Dashboard (рекомендуется)
1. В Railway Dashboard нажмите "New Project"
2. Выберите "Deploy from GitHub repo"
3. Найдите ваш репозиторий
4. Нажмите "Deploy Now"
5. В разделе "Variables" добавьте:
   ```
   TELEGRAM_BOT_TOKEN=ваш_токен
   OPENROUTER_API_KEY=ваш_ключ
   ```

#### Вариант B: Через скрипт
```bash
# Создайте .env файл
echo "TELEGRAM_BOT_TOKEN=ваш_токен" > .env
echo "OPENROUTER_API_KEY=ваш_ключ" >> .env

# Запустите скрипт деплоя
./deploy.sh
```

### 4. Готово! 🎉
Ваш бот работает 24/7 на Railway!

## 🧪 Локальное тестирование

```bash
# Установка
make install

# Запуск
make run

# Тесты
make test
```

## 📊 Мониторинг

- **Railway Dashboard**: https://railway.app/dashboard
- **Логи**: В Railway Dashboard → ваш проект → Deployments → View Logs
- **Метрики**: Автоматически логируются каждый час

## 🆘 Помощь

- **Документация**: [DEPLOY.md](DEPLOY.md)
- **Проблемы**: Проверьте логи в Railway Dashboard
- **Telegram**: Убедитесь что бот не заблокирован

---

**Время деплоя**: ~5 минут  
**Стоимость**: Бесплатно (Hobby план)  
**Uptime**: 99.9%
