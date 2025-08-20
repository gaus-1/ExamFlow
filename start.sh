#!/bin/bash

echo "🚀 Запуск ExamFlow на Render"
echo "================================"

echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

echo "🔄 Собираем статические файлы..."
python manage.py collectstatic --noinput

echo "🔄 Перезагружаем данные бота..."
python manage.py reload_bot_data --force

echo "🔄 Запускаем keep-alive систему..."
python manage.py start_keepalive --daemon --db-interval 300 --site-interval 600 &

echo "🚀 Запускаем сервер Gunicorn..."
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 1
