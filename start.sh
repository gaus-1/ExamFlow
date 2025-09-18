#!/usr/bin/env bash

# Скрипт запуска ExamFlow на Render.com
set -e

echo "🚀 Запуск ExamFlow на Render.com..."

# Проверяем переменные окружения
if [ -z "$DATABASE_URL" ]; then
    echo "❌ DATABASE_URL не установлен"
    exit 1
fi

echo "✅ Переменные окружения настроены"

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install --no-cache-dir -r requirements.txt

# Проверяем миграции
echo "🗄️ Проверяем миграции..."
python manage.py makemigrations --dry-run --check || {
    echo "⚠️ Есть неприменённые миграции, применяем..."
    python manage.py makemigrations
}

# Применяем миграции
echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

# Собираем статические файлы
echo "🎨 Собираем статические файлы..."
python manage.py collectstatic --noinput --clear

# Создаем суперпользователя если нужно (опционально)
echo "👤 Проверяем суперпользователя..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Создаем суперпользователя...')
    User.objects.create_superuser('admin', 'admin@examflow.ru', 'admin123')
    print('✅ Суперпользователь создан')
else:
    print('✅ Суперпользователь уже существует')
" || echo "⚠️ Не удалось создать суперпользователя"

# Загружаем базовые данные
echo "📚 Загружаем базовые данные..."
python manage.py load_sample_data || echo "⚠️ Данные уже загружены"

echo "🌐 Запуск веб-сервера..."

# Запускаем Gunicorn
exec gunicorn examflow_project.wsgi:application \
    --bind 0.0.0.0:$PORT \
    --workers 2 \
    --timeout 120 \
    --max-requests 1000 \
    --max-requests-jitter 100 \
    --preload \
    --access-logfile - \
    --error-logfile -