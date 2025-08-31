# 🚀 Деплой ExamFlow 2.0 на Render

## 📋 Обзор

ExamFlow 2.0 - это платформа лидерского уровня для подготовки к ЕГЭ с интеграцией ИИ-ассистента, современным дизайном и продвинутой архитектурой.

## 🏗️ Архитектура

- **Backend**: Django 4.2.7 + Python 3.11
- **Frontend**: Modern CSS + Vanilla JavaScript
- **AI**: Google Gemini API
- **Database**: PostgreSQL
- **Cache**: Redis
- **Platform**: Render

## 🔧 Требования к деплою

### Переменные окружения

```bash
# Django
SECRET_KEY=<50+ символов, случайных>
DEBUG=false
ALLOWED_HOSTS=examflow.ru,www.examflow.ru,.onrender.com

# База данных
DATABASE_URL=postgresql://user:password@host:port/database

# Redis
REDIS_URL=redis://localhost:6379/0

# AI API
GEMINI_API_KEY=<ваш-ключ-gemini>

# Telegram Bot
TELEGRAM_BOT_TOKEN=<ваш-токен-бота>

# Render
RENDER=true
RENDER_EXTERNAL_HOSTNAME=<app-name>.onrender.com
```

## 🚀 Процесс деплоя

### 1. Подготовка

```bash
# Клонирование репозитория
git clone <repository-url>
cd ExamFlow

# Установка зависимостей
pip install -r requirements-prod.txt

# Проверка конфигурации
python manage.py check --deploy
```

### 2. Настройка Render

1. Создать новый Web Service
2. Подключить Git репозиторий
3. Настроить переменные окружения
4. Указать build и start команды

### 3. Команды деплоя

**Build Command:**
```bash
chmod +x build.sh && ./build.sh
```

**Start Command:**
```bash
chmod +x start.sh && ./start.sh
```

## 📁 Структура файлов деплоя

```
ExamFlow/
├── build.sh              # Скрипт сборки
├── start.sh              # Скрипт запуска
├── render.yaml           # Конфигурация Render
├── requirements-prod.txt # Продакшн зависимости
├── examflow_project/
│   ├── settings.py       # Настройки разработки
│   └── settings_prod.py # Настройки продакшена
└── static/
    └── examflow-2.0/    # Новые статические файлы
```

## 🔒 Безопасность

### Настройки безопасности в продакшене

- `DEBUG = False`
- `SECURE_SSL_REDIRECT = True`
- `SESSION_COOKIE_SECURE = True`
- `CSRF_COOKIE_SECURE = True`
- `X_FRAME_OPTIONS = 'DENY'`
- Content Security Policy (CSP)
- Rate Limiting

### Проверка безопасности

```bash
python manage.py check --deploy
python manage.py check_deploy
```

## 📊 Мониторинг

### Логи

- Логи Django доступны в Render Dashboard
- Уровень логирования: INFO
- Формат: `{levelname} {asctime} {module} {process:d} {thread:d} {message}`

### Метрики

- Время ответа сервера
- Количество запросов
- Использование памяти
- Статус базы данных

## 🚨 Troubleshooting

### Частые проблемы

1. **Ошибка SECRET_KEY**
   - Убедитесь, что SECRET_KEY установлен в переменных окружения
   - Длина должна быть минимум 50 символов

2. **Ошибка базы данных**
   - Проверьте DATABASE_URL
   - Убедитесь, что база данных доступна

3. **Ошибка статических файлов**
   - Проверьте STATIC_ROOT
   - Убедитесь, что collectstatic выполнен

### Команды диагностики

```bash
# Проверка конфигурации
python manage.py check --deploy

# Проверка готовности к деплою
python manage.py check_deploy

# Проверка статических файлов
python manage.py collectstatic --dry-run

# Проверка миграций
python manage.py showmigrations
```

## 🔄 CI/CD Pipeline

### Автоматический деплой

1. Push в main ветку
2. Автоматическая сборка на Render
3. Запуск тестов
4. Деплой в продакшн

### Ручной деплой

```bash
# Создание тега
git tag -a v2.0.0 -m "ExamFlow 2.0 Release"
git push origin v2.0.0

# Деплой через Render Dashboard
```

## 📈 Масштабирование

### Вертикальное масштабирование

- Увеличение RAM и CPU
- Настройка количества workers

### Горизонтальное масштабирование

- Балансировка нагрузки
- Кеширование на уровне CDN
- Оптимизация базы данных

## 🎉 Завершение деплоя

После успешного деплоя:

1. ✅ Проверить доступность сайта
2. ✅ Протестировать все функции
3. ✅ Проверить логи на ошибки
4. ✅ Настроить мониторинг
5. ✅ Обновить DNS записи

---

**Версия**: 2.0.0  
**Дата**: $(date)  
**Автор**: ExamFlow Team
