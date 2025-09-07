#!/bin/bash

echo "🚀 Запускаем ExamFlow на Render..."

# Применяем миграции
echo "🔄 Применяем миграции базы данных..."
python manage.py migrate --noinput

# Собираем статику, чтобы подтянуть последний CSS/JS
echo "📁 Собираем статические файлы..."
python manage.py collectstatic --noinput

# Исправляем предметы - оставляем только математику и русский язык
echo "📚 Исправляем предметы - оставляем только математику и русский язык..."
python manage.py fix_subjects

# Запускаем сервер
echo "🚀 Запускаем сервер..."
gunicorn examflow_project.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --timeout 120
