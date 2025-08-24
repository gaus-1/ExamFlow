#!/usr/bin/env bash
# Build script for Render - автоматически исправляет базу данных

echo "🚀 СБОРКА EXAMFLOW НА RENDER"
echo "================================"

# Активируем виртуальное окружение
echo "📦 Активируем виртуальное окружение..."
source .venv/bin/activate

# Устанавливаем зависимости
echo "📥 Устанавливаем зависимости..."
pip install -r requirements.txt

# ПРИНУДИТЕЛЬНО ИСПРАВЛЯЕМ БАЗУ ДАННЫХ
echo "🔧 Принудительно исправляем базу данных..."
python manage.py fix_database

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
echo "✅ База данных исправлена"
echo "✅ Миграции применены"
echo "✅ Статические файлы собраны"
echo "✅ Готово к запуску!"
