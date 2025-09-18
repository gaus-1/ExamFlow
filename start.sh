#!/bin/bash
# ExamFlow Start Script для Render.com

echo "🚀 Запуск ExamFlow на Render.com..."

# Проверяем переменные окружения
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL не установлен"
    exit 1
fi

if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не установлен"
    exit 1
fi

echo "✅ Переменные окружения настроены"

# Применяем миграции (если нужно)
echo "🗄️ Проверяем миграции..."
python manage.py migrate --check || python manage.py migrate

# Запускаем веб-сервер
echo "🌐 Запуск веб-сервера..."
exec gunicorn examflow_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --access-logfile - \
    --error-logfile -
