# Скрипт для ручного деплоя ExamFlow на Render
Write-Host "🚀 Запуск ручного деплоя ExamFlow на Render..." -ForegroundColor Green

# Проверяем что мы в правильной ветке
$currentBranch = git branch --show-current
if ($currentBranch -ne "main") {
    Write-Host "❌ Ошибка: нужно быть в ветке main, сейчас в $currentBranch" -ForegroundColor Red
    exit 1
}

# Проверяем что нет незакоммиченных изменений
$gitStatus = git status --porcelain
if ($gitStatus) {
    Write-Host "❌ Ошибка: есть незакоммиченные изменения" -ForegroundColor Red
    git status
    exit 1
}

# Коммитим изменения (если есть)
Write-Host "📝 Коммитим изменения..." -ForegroundColor Yellow
$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm"
git add .
git commit -m "Manual deploy: $timestamp"

# Пушим в main
Write-Host "⬆️ Пушим в main..." -ForegroundColor Yellow
git push origin main

Write-Host "✅ Код отправлен в GitHub!" -ForegroundColor Green
Write-Host "🔗 Теперь идите в Render Dashboard для ручного деплоя:" -ForegroundColor Cyan
Write-Host "   https://dashboard.render.com" -ForegroundColor Blue
Write-Host "   → Ваш сервис → Manual Deploy → Deploy latest commit" -ForegroundColor Blue
