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

# Функция для retry операций с базой данных
retry_db_operation() {
    local command="$1"
    local max_attempts=3
    local delay=10
    
    for attempt in $(seq 1 $max_attempts); do
        echo "🔄 Попытка $attempt/$max_attempts: $command"
        
        if eval "$command"; then
            echo "✅ Операция выполнена успешно"
            return 0
        else
            echo "❌ Операция не удалась (попытка $attempt/$max_attempts)"
            if [ $attempt -lt $max_attempts ]; then
                echo "⏳ Ожидание $delay секунд перед повторной попыткой..."
                sleep $delay
                delay=$((delay * 2))  # Exponential backoff
            fi
        fi
    done
    
    echo "💥 Операция не удалась после $max_attempts попыток"
    return 1
}

# Тестируем подключение к базе данных
echo "🔗 Тестируем подключение к базе данных..."
retry_db_operation "python manage.py shell -c \"
from core.database_utils import test_database_connectivity
if not test_database_connectivity():
    exit(1)
\""

# Проверяем миграции
echo "🗄️ Проверяем миграции..."
retry_db_operation "python manage.py makemigrations --dry-run --check" || {
    echo "⚠️ Есть неприменённые миграции, применяем..."
    retry_db_operation "python manage.py makemigrations"
}

# Применяем миграции с помощью специальной команды
echo "🔄 Применяем миграции с retry логикой..."
if python manage.py migrate_render --max-retries=3 --delay=10; then
    echo "✅ Миграции применены успешно"
else
    echo "⚠️ Не удалось применить миграции, пробуем альтернативный подход..."
    
    # Альтернативный подход: применяем миграции по одной
    echo "🔄 Пробуем применить миграции по одной..."
    python manage.py migrate --run-syncdb --noinput || {
        echo "❌ Критическая ошибка: не удалось применить миграции"
        echo "🚀 Запускаем сервер без миграций (в режиме разработки)"
    }
fi

# Собираем статические файлы
echo "🎨 Собираем статические файлы..."
python manage.py collectstatic --noinput --clear

# Создаем суперпользователя если нужно (опционально)
echo "👤 Проверяем суперпользователя..."
retry_db_operation "python manage.py shell -c \"
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Создаем суперпользователя...')
    User.objects.create_superuser('admin', 'admin@examflow.ru', 'admin123')
    print('✅ Суперпользователь создан')
else:
    print('✅ Суперпользователь уже существует')
\"" || echo "⚠️ Не удалось создать суперпользователя"

# Загружаем базовые данные
echo "📚 Загружаем базовые данные..."
retry_db_operation "python manage.py load_sample_data" || echo "⚠️ Данные уже загружены"

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