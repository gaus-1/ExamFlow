"""
Скрипт для настройки автоматического запуска database_keepalive.py

Создаёт задачу в планировщике задач Windows для автоматического
запуска скрипта поддержания активности базы данных каждые 5 минут.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_scheduled_task():
    """Создаёт задачу в планировщике задач Windows"""
    try:
        # Получаем текущий путь к скрипту
        current_dir = Path(__file__).parent.absolute()
        script_path = current_dir / "database_keepalive.py"
        python_exe = sys.executable
        
        # Проверяем существование скрипта
        if not script_path.exists():
            logger.error(f"Скрипт {script_path} не найден!")
            return False
        
        # Создаём команду для создания задачи
        task_name = "ExamFlow_Database_KeepAlive"
        command = [
            "schtasks", "/create", "/tn", task_name,
            "/tr", f'"{python_exe}" "{script_path}"',
            "/sc", "minute", "/mo", "5",
            "/ru", "SYSTEM",
            "/f"  # Принудительно перезаписать существующую задачу
        ]
        
        logger.info("Создаю задачу в планировщике...")
        logger.info(f"Команда: {' '.join(command)}")
        
        # Выполняем команду
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logger.info("✅ Задача успешно создана в планировщике!")
            logger.info(f"Вывод: {result.stdout}")
            return True
        else:
            logger.error(f"❌ Ошибка создания задачи: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при создании задачи: {e}")
        return False

def check_scheduled_task():
    """Проверяет существование задачи в планировщике"""
    try:
        task_name = "ExamFlow_Database_KeepAlive"
        command = ["schtasks", "/query", "/tn", task_name]
        
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logger.info("✅ Задача найдена в планировщике:")
            logger.info(result.stdout)
            return True
        else:
            logger.info("❌ Задача не найдена в планировщике")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при проверке задачи: {e}")
        return False

def delete_scheduled_task():
    """Удаляет задачу из планировщика"""
    try:
        task_name = "ExamFlow_Database_KeepAlive"
        command = ["schtasks", "/delete", "/tn", task_name, "/f"]
        
        logger.info("Удаляю задачу из планировщика...")
        result = subprocess.run(command, capture_output=True, text=True, shell=True)
        
        if result.returncode == 0:
            logger.info("✅ Задача успешно удалена из планировщика!")
            return True
        else:
            logger.error(f"❌ Ошибка удаления задачи: {result.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка при удалении задачи: {e}")
        return False

def create_batch_file():
    """Создаёт .bat файл для ручного запуска"""
    try:
        current_dir = Path(__file__).parent.absolute()
        script_path = current_dir / "database_keepalive.py"
        python_exe = sys.executable
        
        batch_content = f"""@echo off
echo Запуск ExamFlow Database KeepAlive...
echo Python: {python_exe}
echo Скрипт: {script_path}
echo.
cd /d "{current_dir}"
"{python_exe}" "{script_path}"
pause
"""
        
        batch_path = current_dir / "run_database_keepalive.bat"
        
        with open(batch_path, 'w', encoding='utf-8') as f:
            f.write(batch_content)
        
        logger.info(f"✅ Создан .bat файл: {batch_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании .bat файла: {e}")
        return False

def create_powershell_script():
    """Создаёт PowerShell скрипт для запуска"""
    try:
        current_dir = Path(__file__).parent.absolute()
        script_path = current_dir / "database_keepalive.py"
        python_exe = sys.executable
        
        ps_content = f"""# ExamFlow Database KeepAlive PowerShell Script
Write-Host "Запуск ExamFlow Database KeepAlive..." -ForegroundColor Green
Write-Host "Python: {python_exe}" -ForegroundColor Yellow
Write-Host "Скрипт: {script_path}" -ForegroundColor Yellow
Write-Host ""

# Переходим в директорию проекта
Set-Location "{current_dir}"

# Запускаем скрипт
& "{python_exe}" "{script_path}"

Write-Host "Скрипт завершён. Нажмите любую клавишу для выхода..." -ForegroundColor Cyan
Read-Host
"""
        
        ps_path = current_dir / "run_database_keepalive.ps1"
        
        with open(ps_path, 'w', encoding='utf-8') as f:
            f.write(ps_content)
        
        logger.info(f"✅ Создан PowerShell скрипт: {ps_path}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при создании PowerShell скрипта: {e}")
        return False

def main():
    """Основная функция"""
    logger.info("🚀 Настройка автоматического запуска database_keepalive.py")
    logger.info("=" * 60)
    
    # Проверяем права администратора
    try:
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        if not is_admin:
            logger.warning("⚠️ Для создания задачи в планировщике требуются права администратора")
            logger.info("Создаю альтернативные способы запуска...")
            
            # Создаём .bat и .ps1 файлы
            create_batch_file()
            create_powershell_script()
            
            logger.info("\n📋 Инструкции по настройке:")
            logger.info("1. Запустите PowerShell от имени администратора")
            logger.info("2. Выполните команду:")
            logger.info(f'   schtasks /create /tn "ExamFlow_Database_KeepAlive" /tr "python {Path(__file__).parent / "database_keepalive.py"}" /sc minute /mo 5 /ru SYSTEM /f')
            logger.info("3. Или используйте созданные файлы для ручного запуска")
            
        else:
            logger.info("✅ Запуск с правами администратора")
            
            # Проверяем существующую задачу
            if check_scheduled_task():
                logger.info("Задача уже существует. Хотите пересоздать? (y/n): ")
                response = input().lower().strip()
                if response == 'y':
                    delete_scheduled_task()
                    create_scheduled_task()
                else:
                    logger.info("Задача оставлена без изменений")
            else:
                # Создаём новую задачу
                create_scheduled_task()
            
            # Создаём альтернативные способы запуска
            create_batch_file()
            create_powershell_script()
    
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        logger.info("Создаю альтернативные способы запуска...")
        create_batch_file()
        create_powershell_script()
    
    logger.info("\n🎯 Готово! Теперь у вас есть несколько способов запуска:")
    logger.info("1. Автоматически через планировщик задач Windows")
    logger.info("2. Ручной запуск через .bat файл")
    logger.info("3. Ручной запуск через PowerShell скрипт")
    logger.info("4. Прямой запуск: python database_keepalive.py")

if __name__ == "__main__":
    main()
