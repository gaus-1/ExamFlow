"""
Команда для проверки конфигурации Telegram бота
Проверяет наличие токена и доступность бота
"""

from django.core.management.base import BaseCommand
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Проверяет конфигурацию Telegram бота'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Проверка конфигурации Telegram бота')
        self.stdout.write('=' * 50)

        # Проверяем токен
        token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
        if token:
            self.stdout.write('✅ TELEGRAM_BOT_TOKEN: {token[:10]}...')
            logger.info('TELEGRAM_BOT_TOKEN настроен: {token[:10]}...')
        else:
            self.stdout.write('❌ TELEGRAM_BOT_TOKEN не настроен!')
            self.stdout.write('   Добавьте TELEGRAM_BOT_TOKEN в Environment Variables')
            logger.error('TELEGRAM_BOT_TOKEN не настроен')
            return

        # Проверяем SITE_URL
        site_url = getattr(settings, 'SITE_URL', None)
        if site_url:
            self.stdout.write('✅ SITE_URL: {site_url}')
        else:
            self.stdout.write('❌ SITE_URL не настроен!')
            self.stdout.write('   Добавьте SITE_URL в Environment Variables')
            logger.error('SITE_URL не настроен')
            return

        # Проверяем базу данных
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            self.stdout.write('✅ База данных доступна')
            logger.info('База данных доступна')
        except Exception:
            self.stdout.write('❌ Ошибка базы данных: {e}')
            logger.error('Ошибка базы данных: {e}')
            return

        # Проверяем доступность бота
        try:
            from telegram_bot.bot_main import get_bot
            bot = get_bot()
            # get_me() - асинхронная функция, нужно использовать синхронно
            import asyncio
            bot_info = asyncio.run(bot.get_me())
            self.stdout.write('✅ Бот доступен: @{bot_info.username}')
            logger.info('Бот доступен: @{bot_info.username}')
        except Exception:
            self.stdout.write('❌ Ошибка бота: {e}')
            logger.error('Ошибка бота: {e}')
            return

        self.stdout.write('=' * 50)
        self.stdout.write('🎉 Конфигурация бота корректна!')
        logger.info('Конфигурация бота проверена успешно')
