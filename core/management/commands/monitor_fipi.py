"""
Команда для мониторинга обновлений ФИПИ
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from core.fipi_monitor import fipi_monitor
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Мониторинг обновлений ФИПИ для математики и русского языка'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check',
            action='store_true',
            help='Проверить обновления один раз',
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Показать статистику обновлений',
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Запустить непрерывный мониторинг',
        )

    def handle(self, *args, **options):
        if options['check']:
            self.check_updates()
        elif options['stats']:
            self.show_statistics()
        elif options['continuous']:
            self.continuous_monitoring()
        else:
            self.stdout.write(
                self.style.WARNING('Используйте --check, --stats или --continuous')
            )

    def check_updates(self):
        """Проверяет обновления один раз"""
        self.stdout.write('Проверяем обновления ФИПИ...')

        try:
            updates = fipi_monitor.check_for_updates()

            if updates.get('error'):
                self.stdout.write(
                    self.style.ERROR('Ошибка: {updates["error"]}')
                )
                return

            if updates['total_updates'] > 0:
                self.stdout.write(self.style.SUCCESS(
                    'Найдено обновлений: {updates["total_updates"]}'))

                # Показываем обновления по математике
                if updates['math_updates']:
                    self.stdout.write('\n📐 МАТЕМАТИКА:')
                    for update in updates['math_updates']:
                        self.stdout.write('  • {update["title"]}')
                        self.stdout.write('    URL: {update["url"]}')

                # Показываем обновления по русскому языку
                if updates['russian_updates']:
                    self.stdout.write('\n📝 РУССКИЙ ЯЗЫК:')
                    for update in updates['russian_updates']:
                        self.stdout.write('  • {update["title"]}')
                        self.stdout.write('    URL: {update["url"]}')

                self.stdout.write(
                    self.style.SUCCESS('\nАдминистратор уведомлен об обновлениях')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Обновлений не найдено')
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Ошибка при проверке обновлений: {e}')
            )
            logger.error('Ошибка при проверке обновлений: {e}')

    def show_statistics(self):
        """Показывает статистику обновлений"""
        self.stdout.write('Статистика обновлений ФИПИ:')

        try:
            stats = fipi_monitor.get_update_statistics()

            self.stdout.write('Всего обновлений: {stats.get("total_updates", 0)}')
            self.stdout.write(
                'Обновлений по математике: {stats.get("math_updates", 0)}')
            self.stdout.write(
                'Обновлений по русскому языку: {stats.get("russian_updates", 0)}')

            if stats.get('last_check'):
                self.stdout.write('Последняя проверка: {stats["last_check"]}')
            else:
                self.stdout.write('Проверки еще не проводились')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Ошибка при получении статистики: {e}')
            )
            logger.error('Ошибка при получении статистики: {e}')

    def continuous_monitoring(self):
        """Запускает непрерывный мониторинг"""
        self.stdout.write('Запускаем непрерывный мониторинг ФИПИ...')
        self.stdout.write('Нажмите Ctrl+C для остановки')

        try:
            import time

            while True:
                self.stdout.write('\n[{timezone.now()}] Проверяем обновления...')

                updates = fipi_monitor.check_for_updates()

                if updates.get('error'):
                    self.stdout.write(
                        self.style.ERROR('Ошибка: {updates["error"]}')
                    )
                elif updates['total_updates'] > 0:
                    self.stdout.write(
                        self.style.SUCCESS('Найдено обновлений: {updates["total_updates"]}'))
                else:
                    self.stdout.write('Обновлений не найдено')

                # Ждем до следующей проверки
                self.stdout.write(
                    'Следующая проверка через {fipi_monitor.check_interval} секунд...')
                time.sleep(fipi_monitor.check_interval)

        except KeyboardInterrupt:
            self.stdout.write('\nМониторинг остановлен')
        except Exception as e:
            self.stdout.write(
                self.style.ERROR('Ошибка при непрерывном мониторинге: {e}')
            )
            logger.error('Ошибка при непрерывном мониторинге: {e}')
