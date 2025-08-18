#!/usr/bin/env python3
"""
Скрипт для запуска парсинга и загрузки материалов ФИПИ
Запускается автоматически после деплоя
"""

import os
import sys
import subprocess
import time
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_command(command, description):
    """Запуск команды с логированием"""
    logger.info(f"🔄 {description}...")
    logger.info(f"Команда: {command}")
    
    try:
        result = subprocess.run(
            command.split(),
            capture_output=True,
            text=True,
            timeout=600  # 10 минут таймаут
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - УСПЕШНО")
            if result.stdout:
                logger.info(f"Вывод: {result.stdout[:500]}...")
            return True
        else:
            logger.error(f"❌ {description} - ОШИБКА")
            logger.error(f"Код ошибки: {result.returncode}")
            if result.stderr:
                logger.error(f"Ошибка: {result.stderr[:500]}...")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏰ {description} - ТАЙМАУТ (превышено 10 минут)")
        return False
    except Exception as e:
        logger.error(f"💥 {description} - ИСКЛЮЧЕНИЕ: {str(e)}")
        return False


def main():
    """Основная функция парсинга"""
    logger.info("🚀 ЗАПУСК ПАРСИНГА МАТЕРИАЛОВ ФИПИ")
    logger.info("=" * 50)
    
    # Ждем готовности системы
    logger.info("⏳ Ожидание готовности системы...")
    time.sleep(5)
    
    # Список команд для выполнения
    commands = [
        {
            'cmd': 'python manage.py migrate',
            'desc': 'Применение миграций базы данных'
        },
        {
            'cmd': 'python manage.py load_sample_data',
            'desc': 'Загрузка базовых данных'
        },
        {
            'cmd': 'python manage.py load_fipi_data --subjects математика физика химия',
            'desc': 'Парсинг материалов ФИПИ (основные предметы)'
        },
        {
            'cmd': 'python manage.py load_fipi_data --subjects биология история обществознание',
            'desc': 'Парсинг материалов ФИПИ (гуманитарные предметы)'
        },
        {
            'cmd': 'python manage.py load_fipi_data --subjects русский_язык информатика',
            'desc': 'Парсинг материалов ФИПИ (языки и IT)'
        }
    ]
    
    success_count = 0
    total_commands = len(commands)
    
    for i, command_info in enumerate(commands, 1):
        logger.info(f"\n📋 Шаг {i}/{total_commands}: {command_info['desc']}")
        
        if run_command(command_info['cmd'], command_info['desc']):
            success_count += 1
        else:
            logger.warning(f"⚠️ Пропускаем шаг {i} из-за ошибки")
            # Продолжаем выполнение остальных команд
    
    # Дополнительные команды (если основные прошли успешно)
    if success_count >= 2:  # Если хотя бы миграции и базовые данные загружены
        additional_commands = [
            {
                'cmd': 'python manage.py generate_voices --limit 50',
                'desc': 'Генерация голосовых подсказок (первые 50)'
            },
            {
                'cmd': 'python manage.py setup_webhook set',
                'desc': 'Настройка Telegram webhook'
            }
        ]
        
        for command_info in additional_commands:
            logger.info(f"\n🔧 Дополнительно: {command_info['desc']}")
            run_command(command_info['cmd'], command_info['desc'])
    
    # Итоговый отчет
    logger.info("\n" + "=" * 50)
    logger.info(f"📊 ИТОГИ ПАРСИНГА:")
    logger.info(f"✅ Успешно выполнено: {success_count}/{total_commands} команд")
    
    if success_count == total_commands:
        logger.info("🎉 ВСЕ КОМАНДЫ ВЫПОЛНЕНЫ УСПЕШНО!")
        logger.info("🌐 Материалы ФИПИ загружены на сайт")
        logger.info("🤖 Telegram бот настроен")
        logger.info("🎤 Голосовые подсказки готовы")
    elif success_count >= 2:
        logger.info("⚠️ ЧАСТИЧНЫЙ УСПЕХ - основные функции работают")
        logger.info("🌐 Сайт готов к использованию")
    else:
        logger.error("❌ КРИТИЧЕСКИЕ ОШИБКИ - требуется ручное вмешательство")
    
    logger.info(f"🔗 Сайт: https://examflow.ru")
    logger.info("📱 Проверьте работу бота через сайт")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️ Прервано пользователем")
    except Exception as e:
        logger.error(f"\n💥 Критическая ошибка: {str(e)}")
        sys.exit(1)
