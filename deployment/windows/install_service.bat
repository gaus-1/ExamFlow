@echo off
REM ExamFlow Bot Service Installer
REM Устанавливает Telegram бота как системный сервис Windows

echo ========================================
echo   ExamFlow Bot Service Installer
echo ========================================

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Требуются права администратора!
    echo Запустите командную строку от имени администратора
    pause
    exit /b 1
)

REM Переходим в корневую директорию проекта
cd /d "%~dp0..\.."

REM Проверяем наличие файлов
if not exist "venv\Scripts\python.exe" (
    echo ОШИБКА: Виртуальное окружение не найдено!
    echo Создайте venv в корне проекта
    pause
    exit /b 1
)

if not exist "telegram_bot\bot_24_7.py" (
    echo ОШИБКА: Файл бота не найден!
    pause
    exit /b 1
)

REM Устанавливаем NSSM (Non-Sucking Service Manager)
echo Устанавливаем NSSM...
if not exist "deployment\windows\nssm.exe" (
    echo Скачиваем NSSM...
    powershell -Command "Invoke-WebRequest -Uri 'https://nssm.cc/release/nssm-2.24.zip' -OutFile 'nssm.zip'"
    powershell -Command "Expand-Archive -Path 'nssm.zip' -DestinationPath '.'"
    copy "nssm-2.24\win64\nssm.exe" "deployment\windows\nssm.exe"
    rmdir /s /q "nssm-2.24"
    del "nssm.zip"
)

REM Останавливаем существующий сервис (если есть)
echo Останавливаем существующий сервис...
deployment\windows\nssm.exe stop ExamFlowBot 2>nul

REM Удаляем существующий сервис
echo Удаляем существующий сервис...
deployment\windows\nssm.exe remove ExamFlowBot confirm 2>nul

REM Создаем новый сервис
echo Создаем сервис ExamFlowBot...
deployment\windows\nssm.exe install ExamFlowBot "%CD%\venv\Scripts\python.exe"
deployment\windows\nssm.exe set ExamFlowBot AppParameters "%CD%\deployment\windows\examflow_bot_service.py"
deployment\windows\nssm.exe set ExamFlowBot AppDirectory "%CD%"
deployment\windows\nssm.exe set ExamFlowBot DisplayName "ExamFlow Telegram Bot"
deployment\windows\nssm.exe set ExamFlowBot Description "24/7 Telegram бот для подготовки к ЕГЭ и ОГЭ"
deployment\windows\nssm.exe set ExamFlowBot Start SERVICE_AUTO_START
deployment\windows\nssm.exe set ExamFlowBot AppStdout "%CD%\logs\bot_service.log"
deployment\windows\nssm.exe set ExamFlowBot AppStderr "%CD%\logs\bot_service_error.log"
deployment\windows\nssm.exe set ExamFlowBot AppRotateFiles 1
deployment\windows\nssm.exe set ExamFlowBot AppRotateOnline 1
deployment\windows\nssm.exe set ExamFlowBot AppRotateSeconds 86400
deployment\windows\nssm.exe set ExamFlowBot AppRotateBytes 10485760

REM Настраиваем переменные окружения
deployment\windows\nssm.exe set ExamFlowBot AppEnvironmentExtra "DJANGO_SETTINGS_MODULE=examflow_project.settings"

REM Создаем директорию логов
if not exist "logs" mkdir logs

REM Запускаем сервис
echo Запускаем сервис...
deployment\windows\nssm.exe start ExamFlowBot

REM Проверяем статус
timeout /t 5 /nobreak >nul
deployment\windows\nssm.exe status ExamFlowBot

echo.
echo ========================================
echo   Установка завершена!
echo ========================================
echo.
echo Сервис ExamFlowBot установлен и запущен
echo.
echo Управление сервисом:
echo   Запуск:    deployment\windows\nssm.exe start ExamFlowBot
echo   Остановка: deployment\windows\nssm.exe stop ExamFlowBot
echo   Статус:    deployment\windows\nssm.exe status ExamFlowBot
echo   Удаление:  deployment\windows\nssm.exe remove ExamFlowBot confirm
echo.
echo Логи находятся в папке logs\
echo.
pause
