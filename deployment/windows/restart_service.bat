@echo off
REM Перезапуск ExamFlow Bot Service

echo ========================================
echo   Перезапуск ExamFlow Bot Service
echo ========================================

REM Проверяем права администратора
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ОШИБКА: Требуются права администратора!
    echo Запустите от имени администратора
    pause
    exit /b 1
)

echo Останавливаем сервис...
deployment\windows\nssm.exe stop ExamFlowBot

echo Ждем 3 секунды...
timeout /t 3 /nobreak >nul

echo Запускаем сервис...
deployment\windows\nssm.exe start ExamFlowBot

echo Проверяем статус...
timeout /t 2 /nobreak >nul
deployment\windows\nssm.exe status ExamFlowBot

echo.
echo ========================================
echo   Перезапуск завершен!
echo ========================================
echo.
pause
