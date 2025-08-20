#!/bin/bash

echo "🚀 Запуск ExamFlow на Render"
echo "================================"

echo "🔍 Проверяем переменные окружения..."
echo "   TELEGRAM_BOT_TOKEN: ${TELEGRAM_BOT_TOKEN:+✅ НАСТРОЕН (${TELEGRAM_BOT_TOKEN:0:10}...)}"
echo "   SITE_URL: ${SITE_URL:+✅ НАСТРОЕН ($SITE_URL)}"
echo "   RENDER_EXTERNAL_HOSTNAME: ${RENDER_EXTERNAL_HOSTNAME:+✅ НАСТРОЕН ($RENDER_EXTERNAL_HOSTNAME)}"

echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

echo "🔄 Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "🔄 Проверяем настройки бота..."
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN не настроен! Бот не будет работать."
    echo "   Добавьте TELEGRAM_BOT_TOKEN в Environment Variables Render"
    echo "   Переменная должна называться точно: TELEGRAM_BOT_TOKEN"
else
    echo "✅ TELEGRAM_BOT_TOKEN настроен: ${TELEGRAM_BOT_TOKEN:0:10}..."
    echo "🔄 Запускаем полную диагностику бота..."
    python manage.py diagnose_bot
    echo "🔄 Перезагружаем данные бота..."
    python manage.py reload_bot_data --force
    echo "🔄 Проверяем и настраиваем webhook..."
    python manage.py check_webhook
fi

echo "🔄 Проверяем SITE_URL..."
if [ -z "$SITE_URL" ]; then
    echo "⚠️  SITE_URL не настроен, используем RENDER_EXTERNAL_HOSTNAME"
    if [ -n "$RENDER_EXTERNAL_HOSTNAME" ]; then
        export SITE_URL="https://$RENDER_EXTERNAL_HOSTNAME"
        echo "✅ SITE_URL установлен: $SITE_URL"
    else
        echo "❌ RENDER_EXTERNAL_HOSTNAME тоже не настроен!"
    fi
else
    echo "✅ SITE_URL настроен: $SITE_URL"
fi

echo "🔄 Запускаем keep-alive систему..."
python manage.py start_keepalive --daemon --db-interval 300 --site-interval 600 &

echo "🚀 Запускаем сервер Gunicorn..."
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1
