@echo off
echo 🚀 Настройка Ollama для ExamFlow...
echo.

cd /d "%~dp0"
call .venv\Scripts\Activate.bat

echo.
echo 🧹 Очистка старых провайдеров и инициализация Ollama...
python cleanup_old_providers.py

echo.
echo ✅ Настройка завершена!
echo.
echo 🚀 Следующие шаги:
echo 1. Установите Ollama с https://ollama.ai/download
echo 2. Запустите: ollama run llama3.1:8b
echo 3. Перезапустите Django сервер
echo 4. Тестируйте ИИ на сайте!
echo.
pause

