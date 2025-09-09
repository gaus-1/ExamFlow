"""
Команда для управления системой Change Data Capture
"""

from django.core.management.base import BaseCommand

from core.data_ingestion.change_detector import get_cdc_service


class Command(BaseCommand):
    help = 'Управляет системой мониторинга изменений'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'check', 'stats', 'recent'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--source-ids',
            nargs='+',
            help='ID источников для проверки'
        )
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Количество часов для получения недавних изменений'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Мониторить в реальном времени'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'start':
            self.start_service()
        elif action == 'stop':
            self.stop_service()
        elif action == 'status':
            self.show_status()
        elif action == 'check':
            self.check_changes(options)
        elif action == 'stats':
            self.show_statistics()
        elif action == 'recent':
            self.show_recent_changes(options)

    def start_service(self):
        """Запускает сервис мониторинга изменений"""
        self.stdout.write(
            self.style.SUCCESS(
                '🔄 Запуск системы мониторинга изменений...')  # type: ignore
        )

        try:
            from core.data_ingestion.change_detector import start_change_monitoring
            start_change_monitoring()
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Система мониторинга изменений запущена')  # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при запуске: {e}')  # type: ignore
            )

    def stop_service(self):
        """Останавливает сервис мониторинга изменений"""
        self.stdout.write(
            self.style.WARNING(
                '🛑 Остановка системы мониторинга изменений...')  # type: ignore
        )

        try:
            from core.data_ingestion.change_detector import stop_change_monitoring
            stop_change_monitoring()
            self.stdout.write(
                self.style.SUCCESS(
                    '✅ Система мониторинга изменений остановлена')  # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при остановке: {e}')  # type: ignore
            )

    def show_status(self):
        """Показывает статус системы"""
        self.stdout.write(
            self.style.SUCCESS('📊 Статус системы мониторинга изменений')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_cdc_service()

            status_icon = "🟢" if service.is_running else "🔴"
            self.stdout.write(
                f'Сервис: {status_icon} {"Запущен" if service.is_running else "Остановлен"}')  # type: ignore
            self.stdout.write(f'Интервал проверки: {service.check_interval} секунд')

            if service.is_running:
                stats = service.get_statistics()
                detector_stats = stats['detector_stats']

                self.stdout.write('\n📈 Статистика:')
                self.stdout.write(
                    f'  Всего изменений: {detector_stats["total_changes"]}')
                self.stdout.write(f'  Размер очереди: {detector_stats["queue_size"]}')
                self.stdout.write(f'  Недавних изменений: {stats["recent_changes"]}')

                change_counts = detector_stats['change_counts']
                if any(change_counts.values()):
                    self.stdout.write('\n📋 Изменения по типам:')
                    for change_type, count in change_counts.items():
                        if count > 0:
                            icon = {
                                'new': '🆕',
                                'updated': '🔄',
                                'deleted': '🗑️'
                            }.get(change_type, '📌')
                            self.stdout.write(f'  {icon} {change_type}: {count}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при получении статуса: {e}')  # type: ignore
            )

    def check_changes(self, options):
        """Принудительно проверяет изменения"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Принудительная проверка изменений...')  # type: ignore
        )

        try:
            service = get_cdc_service()
            source_ids = options.get('source_ids')

            changes = service.force_check(source_ids)

            if not changes:
                self.stdout.write(
                    self.style.SUCCESS('✅ Изменений не обнаружено')
                )
                return

            self.stdout.write(
                self.style.SUCCESS(f'🔄 Обнаружено {len(changes)} изменений:')
            )
            self.stdout.write('')

            for change in changes:
                icon = {
                    'new': '🆕',
                    'updated': '🔄',
                    'deleted': '🗑️'
                }.get(change.change_type.value, '📌')

                self.stdout.write(f'{icon} {change.source_id}')
                self.stdout.write(f'   Тип: {change.change_type.value}')
                self.stdout.write(f'   URL: {change.url}')
                self.stdout.write(
                    f'   Время: {change.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
                if change.metadata.get('subject'):
                    self.stdout.write(f'   Предмет: {change.metadata["subject"]}')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при проверке изменений: {e}')
            )

    def show_statistics(self):
        """Показывает подробную статистику"""
        self.stdout.write(
            self.style.SUCCESS(
                '📈 Подробная статистика системы мониторинга')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_cdc_service()
            stats = service.get_statistics()

            # Статус сервиса
            self.stdout.write('🔧 Сервис:')
            self.stdout.write(
                f'  Статус: {"🟢 Запущен" if stats["is_running"] else "🔴 Остановлен"}')
            self.stdout.write(f'  Интервал проверки: {stats["check_interval"]} сек')

            # Статистика детектора
            detector_stats = stats['detector_stats']
            self.stdout.write('\n📊 Детектор изменений:')
            self.stdout.write(f'  Всего изменений: {detector_stats["total_changes"]}')
            self.stdout.write(f'  Размер очереди: {detector_stats["queue_size"]}')

            change_counts = detector_stats['change_counts']
            self.stdout.write('\n📋 Изменения по типам:')
            for change_type, count in change_counts.items():
                icon = {
                    'new': '🆕',
                    'updated': '🔄',
                    'deleted': '🗑️'
                }.get(change_type, '📌')
                self.stdout.write(f'  {icon} {change_type}: {count}')

            # Недавние изменения
            self.stdout.write(f'\n⏰ Недавние изменения: {stats["recent_changes"]}')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при получении статистики: {e}')
            )

    def show_recent_changes(self, options):
        """Показывает недавние изменения"""
        hours = options['hours']

        self.stdout.write(
            self.style.SUCCESS(
                f'⏰ Недавние изменения за последние {hours} часов')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_cdc_service()
            recent_changes = service.detector.get_recent_changes(hours)

            if not recent_changes:
                self.stdout.write(
                    self.style.SUCCESS('✅ Недавних изменений не найдено')
                )
                return

            self.stdout.write(f'📋 Найдено {len(recent_changes)} изменений:')
            self.stdout.write('')

            for change in recent_changes:
                icon = {
                    'new': '🆕',
                    'updated': '🔄',
                    'deleted': '🗑️'
                }.get(change.change_type.value, '📌')

                self.stdout.write(f'{icon} {change.source_id}')
                self.stdout.write(f'   Тип: {change.change_type.value}')
                self.stdout.write(f'   URL: {change.url}')
                self.stdout.write(
                    f'   Время: {change.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')
                if change.metadata.get('subject'):
                    self.stdout.write(f'   Предмет: {change.metadata["subject"]}')
                if change.metadata.get('data_type'):
                    self.stdout.write(f'   Тип данных: {change.metadata["data_type"]}')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при получении недавних изменений: {e}')
            )
