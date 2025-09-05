#!/bin/bash

echo "🚀 Запускаем ExamFlow на Render..."

# Применяем миграции
echo "🔄 Применяем миграции базы данных..."
python manage.py migrate --noinput

# Инициализируем предметы
echo "📚 Инициализируем предметы математики и русского языка..."
python manage.py simple_init_subjects

# Запускаем сервер
echo "🚀 Запускаем сервер..."
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
