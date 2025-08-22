@echo off
echo Тестирование ИИ модуля ExamFlow...
cd /d "%~dp0"
call .venv\Scripts\Activate.bat
python test_ai_working.py
pause
