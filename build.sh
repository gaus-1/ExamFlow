#!/usr/bin/env bash
# Build script for Render - автоматически применяет миграции

echo "🚀 СБОРКА EXAMFLOW НА RENDER"
echo "================================"

# Активируем виртуальное окружение
echo "📦 Активируем виртуальное окружение..."
source .venv/bin/activate

# Устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install -r requirements.txt

# Применяем миграции
echo "🔄 Применяем миграции..."
python manage.py migrate --noinput

# Собираем статические файлы
echo "🎨 Собираем статические файлы..."
python manage.py collectstatic --noinput

# Проверяем статус миграций
echo "✅ Проверяем статус миграций..."
python manage.py showmigrations

echo "================================"
echo "🎉 СБОРКА ЗАВЕРШЕНА!"
echo "✅ Миграции применены"
echo "✅ Статические файлы собраны"
echo "✅ Готово к запуску!"
