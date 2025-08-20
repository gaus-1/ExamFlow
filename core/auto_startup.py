"""
Автоматический запуск задач при старте Django приложения
Запускается при первом запросе к сайту (бесплатно)
"""

import os
import logging
import threading
from django.core.management import call_command
from django.conf import settings
from django.db import connection
from core.models import Subject, Task

logger = logging.getLogger(__name__)

# Флаг для предотвращения повторного запуска
_startup_executed = False
_startup_lock = threading.Lock()


def should_run_startup():
    """Проверяет, нужно ли запускать автозапуск"""
    # Проверяем переменную окружения
    auto_startup = os.getenv('AUTO_STARTUP_ENABLED', 'true').lower()
    if auto_startup not in ['true', '1', 'yes']:
        logger.info("Автозапуск отключен через AUTO_STARTUP_ENABLED")
        return False
    
    # Проверяем, есть ли уже данные
    try:
        subjects_count = Subject.objects.count()
        tasks_count = Task.objects.count()
        
        logger.info(f"Текущее состояние: {subjects_count} предметов, {tasks_count} заданий")
        
        # Если данных мало, запускаем парсинг
        if subjects_count < 3 or tasks_count < 10:
            logger.info("Данных недостаточно, запускаем автозагрузку")
            return True
        else:
            logger.info("Данные уже загружены, пропускаем автозапуск")
            return False
            
    except Exception as e:
        logger.error(f"Ошибка проверки данных: {str(e)}")
        return True  # В случае ошибки пытаемся загрузить


def run_startup_tasks():
    """Выполняет задачи автозапуска"""
    global _startup_executed
    
    with _startup_lock:
        if _startup_executed:
            return
        
        logger.info("🚀 Запуск автоматических задач при старте...")
        
        try:
            # 1. Применяем миграции
            logger.info("📋 Применение миграций...")
            call_command('migrate', verbosity=0)
            
            # 2. Загружаем базовые данные
            logger.info("📊 Загрузка базовых данных...")
            call_command('load_sample_data', verbosity=0)
            
            # 3. Быстрый парсинг ФИПИ (только основные предметы)
            logger.info("🔥 Быстрый парсинг материалов ФИПИ...")
            call_command('parse_all_fipi', quick=True, verbosity=1)
            
            # 4. Настройка webhook
            logger.info("🤖 Настройка Telegram webhook...")
            try:
                call_command('setup_webhook', 'set', verbosity=0)
            except Exception as e:
                logger.warning(f"Ошибка настройки webhook: {str(e)}")
            
            # 5. Генерация голосовых подсказок (ограниченно)
            logger.info("🎤 Генерация голосовых подсказок...")
            try:
                call_command('generate_voices', limit=20, verbosity=0)
            except Exception as e:
                logger.warning(f"Ошибка генерации голоса: {str(e)}")
            
            # 6. Запуск keep-alive (поддержание активности и еженедельные напоминания)
            try:
                from core.keepalive import start_keepalive  # ленивый импорт, чтобы избежать циклов
                start_keepalive()
                logger.info("🌐 Keep-alive запущен (пинги каждые 10 минут, напоминания по воскресеньям)")
            except Exception as e:
                logger.warning(f"Не удалось запустить keep-alive: {str(e)}")
            
            _startup_executed = True
            logger.info("✅ Автозапуск завершен успешно!")
            
            # Логируем финальную статистику
            subjects_count = Subject.objects.count()
            tasks_count = Task.objects.count()
            logger.info(f"📊 Итого: {subjects_count} предметов, {tasks_count} заданий")
            
        except Exception as e:
            logger.error(f"❌ Ошибка автозапуска: {str(e)}")
            _startup_executed = True  # Помечаем как выполненное, чтобы не повторять


def run_startup_in_background():
    """Запускает автозапуск в фоновом потоке"""
    if not should_run_startup():
        return
    
    def background_task():
        # Небольшая задержка для стабилизации
        import time
        time.sleep(2)
        run_startup_tasks()
    
    # Запускаем в отдельном потоке
    thread = threading.Thread(target=background_task, daemon=True)
    thread.start()
    logger.info("🔄 Автозапуск запущен в фоновом режиме...")


def trigger_startup_on_first_request(get_response):
    """Middleware для запуска автозадач при первом запросе"""
    
    def middleware(request):
        global _startup_executed
        
        # Запускаем только при первом запросе
        if not _startup_executed and not request.path.startswith('/admin'):
            run_startup_in_background()
        
        response = get_response(request)
        return response
    
    return middleware
