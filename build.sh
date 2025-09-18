#!/bin/bash
# ExamFlow Build Script для Render.com

echo "🚀 Начинаем сборку ExamFlow..."

# Устанавливаем зависимости
echo "📦 Устанавливаем Python зависимости..."
pip install -r config/requirements.txt

# Собираем статические файлы
echo "📁 Собираем статические файлы..."
python manage.py collectstatic --noinput

# Применяем миграции
echo "🗄️ Применяем миграции базы данных..."
python manage.py migrate

echo "✅ Сборка завершена успешно!"
