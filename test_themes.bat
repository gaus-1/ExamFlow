@echo off
echo Запуск тестирования модуля themes...
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo.
echo Виртуальное окружение активировано
echo.

python test_themes_module.py

echo.
echo Тестирование завершено
pause
