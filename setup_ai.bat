@echo off
echo Настройка ИИ модуля ExamFlow...
cd /d "%~dp0"
call .venv\Scripts\Activate.bat

echo.
echo 1. Создание миграций для ИИ...
python manage.py makemigrations ai

echo.
echo 2. Применение всех миграций...
python manage.py migrate

echo.
echo 3. Проверка статуса Django...
python manage.py check

echo.
echo Настройка завершена!
pause
