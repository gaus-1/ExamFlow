# 🤖 Настройка и запуск Telegram бота ExamFlow

## 📋 Проблема
Бот не отвечает на кнопки при переходе с сайта - нужно запустить процесс бота на сервере.

## 🚀 Решение на Render

### 1. Добавить процесс бота в `Procfile`
```
web: gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1
bot: python bot/bot.py
```

### 2. Создать отдельный сервис для бота
В Render Dashboard:
- Создать новый **Background Worker** 
- Подключить тот же репозиторий
- Команда запуска: `python bot/bot.py`
- Использовать те же переменные окружения

### 3. Переменные окружения (обязательные)
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
DATABASE_URL=your_database_url
SITE_URL=https://examflow.ru
ADMIN_CHAT_ID=your_telegram_chat_id
```

## 🔧 Локальная диагностика

### Проверить статус бота:
```bash
python manage.py runbot status
```

### Запустить бота локально:
```bash
# В интерактивном режиме
python manage.py runbot start

# В фоновом режиме  
python manage.py runbot start --daemon
```

### Остановить бота:
```bash
python manage.py runbot stop
```

### Тестирование:
```bash
python test_bot.py
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
