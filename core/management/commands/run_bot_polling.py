"""
Команда для запуска Telegram бота в режиме polling
Полезно для тестирования и локальной разработки
"""

from django.core.management.base import BaseCommand
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Запускает Telegram бота в режиме polling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--daemon',
            action='store_true',
            help='Запустить в фоновом режиме'
        )

    def handle(self, *args, **options):
        self.stdout.write('🤖 Запуск Telegram бота ExamFlow в режиме polling...')

        try:
            # Проверяем настройки
            from django.conf import settings
            token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not token:
                self.stdout.write('❌ TELEGRAM_BOT_TOKEN не настроен!')
                self.stdout.write(
                    '   Добавьте TELEGRAM_BOT_TOKEN в Environment Variables')
                return

            # Создаем и запускаем бота
            from telegram_bot.bot_main import setup_bot_application

            self.stdout.write('🔄 Настройка бота...')
            application = setup_bot_application()

            self.stdout.write('🚀 Запуск в режиме polling...')
            self.stdout.write('📝 Нажмите Ctrl+C для остановки')

            # Запускаем бота
            application.run_polling(
                allowed_updates=["message", "callback_query"],
                drop_pending_updates=True
            )

        except KeyboardInterrupt:
            self.stdout.write('\n⚠️  Остановка по запросу пользователя...')
        except Exception:
            self.stdout.write('❌ Ошибка запуска бота: {e}')
            logger.error('Ошибка запуска бота: {e}')
