#!/usr/bin/env bash

# Скрипт сборки ExamFlow для Render.com
set -e

echo "🔨 Сборка ExamFlow..."

# Обновляем pip
echo "📦 Обновляем pip..."
pip install --upgrade pip

# Устанавливаем зависимости
echo "📦 Устанавливаем Python зависимости..."
pip install --no-cache-dir -r requirements.txt

# Проверяем установку Django
echo "🔍 Проверяем установку Django..."
python -c "import django; print(f'✅ Django {django.get_version()} установлен')"

# Проверяем установку gunicorn
echo "🔍 Проверяем установку gunicorn..."
python -c "import gunicorn; print('✅ Gunicorn установлен')"

echo "✅ Сборка завершена успешно!"