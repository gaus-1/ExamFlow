#!/bin/bash

echo "🚀 Запускаем ExamFlow на Render..."

# Применяем миграции
echo "🔄 Применяем миграции базы данных..."
python manage.py migrate --noinput

# Запускаем сервер
echo "🚀 Запускаем сервер..."
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
