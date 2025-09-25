#!/bin/bash
# Скрипт для быстрого деплоя на Render

echo "🚀 Быстрый деплой ExamFlow на Render..."

# Проверяем что мы в правильной ветке
if [ "$(git branch --show-current)" != "main" ]; then
    echo "❌ Ошибка: нужно быть в ветке main"
    exit 1
fi

# Проверяем что нет незакоммиченных изменений
if ! git diff-index --quiet HEAD --; then
    echo "❌ Ошибка: есть незакоммиченные изменения"
    git status
    exit 1
fi

# Коммитим изменения
echo "📝 Коммитим изменения..."
git add .
git commit -m "Production deploy: $(date '+%Y-%m-%d %H:%M')"

# Пушим в main
echo "⬆️ Пушим в main..."
git push origin main

echo "✅ Деплой запущен! Проверьте Render Dashboard"
echo "🔗 https://dashboard.render.com"
