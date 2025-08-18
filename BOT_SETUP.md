# 🤖 Настройка Telegram бота ExamFlow через Webhook

## 📋 Проблема
Бот не отвечает на кнопки при переходе с сайта.

## 🚀 Решение через Webhook (БЕСПЛАТНО)

### ✅ Преимущества webhook режима:
- **Бесплатно** - не требует Background Worker
- **Быстрее** - мгновенная обработка
- **Надежнее** - интегрирован с основным процессом
- **Проще** - нет отдельных процессов

### 🔧 Уже настроено:
- ✅ Webhook endpoint: `/bot/webhook/`
- ✅ Обработчики команд и кнопок
- ✅ Интеграция с Django
- ✅ Логирование и обработка ошибок

## ⚡ БЫСТРОЕ РЕШЕНИЕ

### 1. Настроить webhook (одна команда):
```bash
python manage.py setup_webhook set
```

### 2. Переменные окружения (уже настроены):
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=your_database_url
SITE_URL=https://examflow.ru
ADMIN_CHAT_ID=your_telegram_chat_id
```

## 🔧 Команды управления

### Настройка webhook:
```bash
# Установить webhook
python manage.py setup_webhook set

# Проверить статус
python manage.py setup_webhook info

# Удалить webhook (если нужно)
python manage.py setup_webhook delete
```

### Диагностика:
```bash
# Проверить токен и API
python test_bot.py

# Проверить данные
python manage.py load_sample_data
```

## 🐛 Возможные проблемы

### 1. Токен бота не работает
- Проверить токен в @BotFather
- Убедиться, что бот активен
- Проверить переменную TELEGRAM_BOT_TOKEN

### 2. База данных пуста
```bash
python manage.py load_sample_data
python manage.py load_fipi_data --samples-only
```

### 3. Бот не получает обновления
- Проверить webhook: `https://api.telegram.org/bot<TOKEN>/getWebhookInfo`
- Удалить webhook: `https://api.telegram.org/bot<TOKEN>/deleteWebhook`
- Бот использует polling, не webhook

### 4. Ошибки в логах
Проверить логи в Render Dashboard или локально в файле `bot.log`

## 📱 Тестирование переходов с сайта

1. Открыть https://examflow.ru
2. Нажать на кнопку "Telegram Бот" 
3. Перейти в бота
4. Нажать /start
5. Проверить работу кнопок меню

## ⚡ Быстрый фикс

Если бот все еще не работает, выполнить на сервере:
```bash
# Перезапуск всех процессов
python manage.py runbot restart

# Проверка статуса
python manage.py runbot status

# Загрузка данных (если нужно)
python manage.py load_sample_data
```

## 🔍 Проверка API бота
```bash
curl "https://api.telegram.org/bot<YOUR_TOKEN>/getMe"
```

Должен вернуть информацию о боте в формате JSON.
