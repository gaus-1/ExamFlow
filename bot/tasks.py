import threading
import subprocess
import logging
from django.http import HttpResponse
import os

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения процесса бота
bot_process = None

def start_bot():
    """Запуск Telegram-бота в отдельном потоке"""
    global bot_process
    
    # Проверяем, не запущен ли уже бот
    if bot_process and bot_process.poll() is None:
        logger.info("Bot is already running")
        return True
    
    try:
        logger.info("Starting Telegram bot...")
        # Запускаем бота в отдельном процессе
        bot_process = subprocess.Popen(
            ['python', 'bot/bot.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Bot started with PID: {bot_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return False

def stop_bot():
    """Остановка бота"""
    global bot_process
    
    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        finally:
            bot_process = None

def restart_bot():
    """Перезапуск бота"""
    stop_bot()
    return start_bot()

def get_bot_status():
    """Получение статуса бота"""
    global bot_process
    
    if bot_process and bot_process.poll() is None:
        return {
            'status': 'running',
            'pid': bot_process.pid
        }
    else:
        return {
            'status': 'stopped'
        }

def bot_status_view(request):
    """Представление для проверки статуса бота"""
    status = get_bot_status()
    return HttpResponse(f"Bot status: {status['status']}")

def start_bot_view(request):
    """Представление для запуска бота"""
    success = start_bot()
    if success:
        return HttpResponse("Bot started successfully")
    else:
        return HttpResponse("Failed to start bot", status=500)

def restart_bot_view(request):
    """Представление для перезапуска бота"""
    success = restart_bot()
    if success:
        return HttpResponse("Bot restarted successfully")
    else:
        return HttpResponse("Failed to restart bot", status=500)

def stop_bot_view(request):
    """Представление для остановки бота"""
    stop_bot()
    return HttpResponse("Bot stopped")

[Bcat > bot/tasks.py << EOF
import threading
import subprocess
import logging
from django.http import HttpResponse
import os

logger = logging.getLogger(__name__)

# Глобальная переменная для хранения процесса бота
bot_process = None

def start_bot():
    """Запуск Telegram-бота в отдельном потоке"""
    global bot_process
    
    # Проверяем, не запущен ли уже бот
    if bot_process and bot_process.poll() is None:
        logger.info("Bot is already running")
        return True
    
    try:
        logger.info("Starting Telegram bot...")
        # Запускаем бота в отдельном процессе
        bot_process = subprocess.Popen(
            ['python', 'bot/bot.py'],
            cwd=os.path.dirname(os.path.abspath(__file__)),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        logger.info(f"Bot started with PID: {bot_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        return False

def stop_bot():
    """Остановка бота"""
    global bot_process
    
    if bot_process:
        try:
            bot_process.terminate()
            bot_process.wait(timeout=5)
            logger.info("Bot stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping bot: {e}")
        finally:
            bot_process = None

def restart_bot():
    """Перезапуск бота"""
    stop_bot()
    return start_bot()

def get_bot_status():
    """Получение статуса бота"""
    global bot_process
    
    if bot_process and bot_process.poll() is None:
        return {
            'status': 'running',
            'pid': bot_process.pid
        }
    else:
        return {
            'status': 'stopped'
        }

def bot_status_view(request):
    """Представление для проверки статуса бота"""
    status = get_bot_status()
    return HttpResponse(f"Bot status: {status['status']}")

def start_bot_view(request):
    """Представление для запуска бота"""
    success = start_bot()
    if success:
        return HttpResponse("Bot started successfully")
    else:
        return HttpResponse("Failed to start bot", status=500)

def restart_bot_view(request):
    """Представление для перезапуска бота"""
    success = restart_bot()
    if success:
        return HttpResponse("Bot restarted successfully")
    else:
        return HttpResponse("Failed to restart bot", status=500)

def stop_bot_view(request):
    """Представление для остановки бота"""
    stop_bot()
    return HttpResponse("Bot stopped")
