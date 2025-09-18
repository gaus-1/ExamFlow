@echo off
REM Исправление конфликта ботов ExamFlow

echo ========================================
echo   Исправление конфликта ботов
echo ========================================

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Требуются права администратора!
    echo Запустите от имени администратора
    pause
    exit /b 1
)

echo 1. Останавливаем ВСЕ сервисы ExamFlow...
deployment\windows\nssm.exe stop ExamFlowBot 2>nul

echo 2. Удаляем старые сервисы...
deployment\windows\nssm.exe remove ExamFlowBot confirm 2>nul

echo 3. Ждем 5 секунд...
timeout /t 5 /nobreak >nul

echo 4. Создаем НОВЫЙ сервис с правильными параметрами...
deployment\windows\nssm.exe install ExamFlowBot "%CD%\venv\Scripts\python.exe"
deployment\windows\nssm.exe set ExamFlowBot AppParameters "%CD%\start_bot_direct.py"
deployment\windows\nssm.exe set ExamFlowBot AppDirectory "%CD%"
deployment\windows\nssm.exe set ExamFlowBot DisplayName "ExamFlow Telegram Bot (Fixed)"
deployment\windows\nssm.exe set ExamFlowBot Description "24/7 Telegram бот ExamFlow - исправленная версия"
deployment\windows\nssm.exe set ExamFlowBot Start SERVICE_AUTO_START
deployment\windows\nssm.exe set ExamFlowBot AppStdout "%CD%\logs\bot_fixed.log"
deployment\windows\nssm.exe set ExamFlowBot AppStderr "%CD%\logs\bot_fixed_error.log"
deployment\windows\nssm.exe set ExamFlowBot AppRotateFiles 1
deployment\windows\nssm.exe set ExamFlowBot AppRotateOnline 1
deployment\windows\nssm.exe set ExamFlowBot AppRotateSeconds 86400
deployment\windows\nssm.exe set ExamFlowBot AppRotateBytes 10485760
deployment\windows\nssm.exe set ExamFlowBot AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=examflow_project.settings"

echo 5. Запускаем исправленный сервис...
deployment\windows\nssm.exe start ExamFlowBot

echo 6. Проверяем статус...
timeout /t 3 /nobreak >nul
deployment\windows\nssm.exe status ExamFlowBot

echo.
echo ========================================
echo   Исправление завершено!
echo ========================================
echo.
echo Проверьте логи: logs\bot_fixed.log
echo.
pause
