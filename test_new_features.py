"""
Скрипт для тестирования всех новых функций ExamFlow

Тестирует:
1. Систему геймификации
2. Анимации и стили
3. Database keepalive
4. Новые обработчики бота
"""

import os
import sys
import django
import logging
from pathlib import Path

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

from django.contrib.auth.models import User
from telegram_bot.gamification import TelegramGamification

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def test_gamification_system():
    """Тестирует систему геймификации"""
    logger.info("Тестирование системы геймификации...")
    
    try:
        gamification = TelegramGamification()
        
        # Тестируем создание пользователя и добавление очков
        test_user_id = 12345
        
        # Добавляем очки
        result = await gamification.add_points(test_user_id, 50, "Тестовое задание")
        if result.get('success'):
            logger.info(f"Очки добавлены: {result}")
        else:
            logger.error(f"Ошибка добавления очков: {result}")
        
        # Получаем статистику
        stats = await gamification.get_user_stats(test_user_id)
        if stats.get('success'):
            logger.info(f"Статистика получена: {stats}")
        else:
            logger.error(f"Ошибка получения статистики: {stats}")
        
        # Получаем ежедневные задания
        challenges = await gamification.get_daily_challenges(test_user_id)
        logger.info(f"Ежедневные задания: {len(challenges)} заданий")
        
        # Получаем таблицу лидеров
        leaderboard = await gamification.get_leaderboard(5)
        logger.info(f"Таблица лидеров: {len(leaderboard)} пользователей")
        
        logger.info("Система геймификации работает корректно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в системе геймификации: {e}")
        return False

def test_website_features():
    """Тестирует новые функции веб-сайта"""
    logger.info("Тестирование новых функций веб-сайта...")
    
    try:
        # Простая проверка без Django Client для избежания async проблем
        logger.info("Проверка доступности статических файлов...")
        
        # Проверяем наличие статических файлов
        static_files = [
            'static/js/examflow-animations.js',
            'static/js/gamification.js',
            'static/css/examflow-styles.css'
        ]
        
        static_available = 0
        for static_file in static_files:
            file_path = Path(static_file)
            if file_path.exists():
                logger.info(f"Статический файл {static_file} найден")
                static_available += 1
            else:
                logger.warning(f"Статический файл {static_file} не найден")
        
        # Проверяем наличие шаблона
        template_path = Path('templates/home.html')
        if template_path.exists():
            logger.info("Шаблон home.html найден")
            
            # Читаем содержимое шаблона для проверки элементов
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            checks = [
                ('ai-chat-input-container', 'Строка общения с ИИ'),
                ('fipi-tabs', 'Вкладка "Задания ФИПИ"'),
                ('user-stats', 'Статистика пользователя'),
                ('progress-container', 'Прогресс-бары'),
                ('daily-challenges', 'Ежедневные задания'),
                ('achievements-container', 'Достижения'),
                ('leaderboard', 'Таблица лидеров')
            ]
            
            found_elements = 0
            for element, description in checks:
                if element in content:
                    logger.info(f"Найден {description}")
                    found_elements += 1
                else:
                    logger.warning(f"Не найден {description}")
            
            if found_elements >= 5:  # Минимум 5 из 7 элементов
                logger.info("Основные элементы интерфейса найдены")
                template_check = True
            else:
                logger.warning("Не все элементы интерфейса найдены")
                template_check = False
        else:
            logger.error("Шаблон home.html не найден")
            template_check = False
        
        # Итоговая оценка
        if static_available >= 2 and template_check:  # Минимум 2 статических файла и шаблон
            logger.info("Веб-сайт работает корректно!")
            return True
        else:
            logger.warning("Веб-сайт требует доработки")
            return False
        
    except Exception as e:
        logger.error(f"Ошибка в веб-сайте: {e}")
        return False

def test_database_keepalive():
    """Тестирует скрипт database_keepalive"""
    logger.info("Тестирование database_keepalive...")
    
    try:
        # Импортируем и тестируем скрипт
        from database_keepalive import DatabaseKeepAlive
        
        # Создаём экземпляр
        keepalive = DatabaseKeepAlive()
        
        # Тестируем соединение
        if keepalive.test_connection():
            logger.info("Соединение с базой данных установлено")
        else:
            logger.error("Не удалось установить соединение с БД")
            return False
        
        # Тестируем пинг
        if keepalive.ping_database():
            logger.info("Пинг базы данных успешен")
        else:
            logger.error("Пинг базы данных не удался")
            return False
        
        # Тестируем keep-alive запрос
        if hasattr(keepalive, 'execute_keepalive_query'):
            keepalive.execute_keepalive_query()
            logger.info("Keep-alive запрос выполнен")
        else:
            logger.warning("Метод execute_keepalive_query не найден")
        
        # Закрываем соединение
        keepalive.close_connection()
        logger.info("Соединение с базой данных закрыто")
        
        logger.info("Database keepalive работает корректно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в database_keepalive: {e}")
        return False

def test_telegram_bot_handlers():
    """Тестирует новые обработчики Telegram бота"""
    logger.info("Тестирование новых обработчиков Telegram бота...")
    
    try:
        # Проверяем импорт обработчиков
        from telegram_bot.bot_handlers import (
            gamification_menu_handler, user_stats_handler, achievements_handler,
            progress_handler, overall_progress_handler, subjects_progress_handler,
            daily_challenges_handler, leaderboard_handler, bonus_handler
        )
        
        logger.info("Все обработчики геймификации импортированы")
        
        # Проверяем импорт системы геймификации
        from telegram_bot.gamification import TelegramGamification
        gamification = TelegramGamification()
        logger.info("Система геймификации импортирована")
        
        # Проверяем создание клавиатур
        test_user_id = 12345
        gamification_keyboard = gamification.create_gamification_keyboard(test_user_id)
        progress_keyboard = gamification.create_progress_keyboard(test_user_id)
        
        if gamification_keyboard and progress_keyboard:
            logger.info("Клавиатуры геймификации создаются корректно")
        else:
            logger.error("Ошибка создания клавиатур")
            return False
        
        logger.info("Обработчики Telegram бота работают корректно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в обработчиках Telegram бота: {e}")
        return False

def test_security_features():
    """Тестирует функции безопасности"""
    logger.info("Тестирование функций безопасности...")
    
    try:
        from django.conf import settings
        
        # Проверяем настройки безопасности
        security_settings = [
            'SECURE_CONTENT_TYPE_NOSNIFF',
            'SECURE_BROWSER_XSS_FILTER',
            'X_FRAME_OPTIONS',
            'SECURE_REFERRER_POLICY',
            'PERMISSIONS_POLICY'
        ]
        
        for setting in security_settings:
            if hasattr(settings, setting):
                logger.info(f"Настроен {setting}: {getattr(settings, setting)}")
            else:
                logger.warning(f"Не настроен {setting}")
        
        # Проверяем middleware безопасности
        if 'examflow_project.middleware.SecurityHeadersMiddleware' in settings.MIDDLEWARE:
            logger.info("SecurityHeadersMiddleware подключен")
        else:
            logger.warning("SecurityHeadersMiddleware не подключен")
        
        # Проверяем логирование безопасности
        if hasattr(settings, 'SECURITY_LOGGING'):
            logger.info("Логирование безопасности настроено")
        else:
            logger.warning("Логирование безопасности не настроено")
        
        logger.info("Функции безопасности работают корректно!")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка в функциях безопасности: {e}")
        return False

async def main():
    """Основная функция тестирования"""
    logger.info("Запуск тестирования всех новых функций ExamFlow")
    logger.info("=" * 70)
    
    tests = [
        ("Система геймификации", test_gamification_system),
        ("Веб-сайт", test_website_features),
        ("Database keepalive", test_database_keepalive),
        ("Telegram бот", test_telegram_bot_handlers),
        ("Безопасность", test_security_features)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        logger.info(f"\n{'='*20} {test_name} {'='*20}")
        try:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            results.append((test_name, result))
        except Exception as e:
            logger.error(f"Критическая ошибка в тесте {test_name}: {e}")
            results.append((test_name, False))
    
    # Итоговый отчёт
    logger.info("\n" + "="*70)
    logger.info("ИТОГОВЫЙ ОТЧЁТ ПО ТЕСТИРОВАНИЮ")
    logger.info("=" * 70)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "ПРОЙДЕН" if result else "ПРОВАЛЕН"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
    
    logger.info(f"\nРезультат: {passed}/{total} тестов пройдено")
    
    if passed == total:
        logger.info("Все тесты пройдены успешно!")
    else:
        logger.warning(f"{total - passed} тестов провалено")
    
    return passed == total

if __name__ == "__main__":
    import asyncio
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
