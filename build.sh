#!/bin/bash

echo "🚀 Начинаем сборку ExamFlow..."

# Устанавливаем зависимости
echo "📦 Устанавливаем Python зависимости..."
pip install -r requirements-prod.txt

# Применяем миграции
echo "🔄 Применяем миграции базы данных..."
python manage.py migrate --noinput

# Собираем статические файлы
echo "📁 Собираем статические файлы..."
python manage.py collectstatic --noinput

# Проверяем конфигурацию
echo "✅ Проверяем конфигурацию Django..."
python manage.py check --deploy

# Проверяем готовность к деплою
echo "🔍 Проверяем готовность к деплою..."
python manage.py check_deploy

echo "🎉 Сборка завершена успешно!"
