@echo off
echo Тестирование подключения к PostgreSQL...
cd /d "%~dp0"
call .venv\Scripts\Activate.bat
python force_postgres.py
pause
