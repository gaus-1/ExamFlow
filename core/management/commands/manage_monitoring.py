"""
Команда для управления системой мониторинга
"""

from django.core.management.base import BaseCommand

from core.data_ingestion.monitoring import get_monitoring_service, AlertLevel


class Command(BaseCommand):
    help = 'Управляет системой мониторинга'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'health', 'alerts', 'test-alert'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--level',
            choices=['info', 'warning', 'error', 'critical'],
            help='Уровень для тестового уведомления'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Мониторить в реальном времени'
        )

    def handle(self, *args, **options):
        action = options['action']

        if action == 'start':
            self.start_monitoring()
        elif action == 'stop':
            self.stop_monitoring()
        elif action == 'status':
            self.show_status()
        elif action == 'health':
            self.show_health()
        elif action == 'alerts':
            self.show_alerts()
        elif action == 'test-alert':
            self.test_alert(options)

    def start_monitoring(self):
        """Запускает систему мониторинга"""
        self.stdout.write(
            self.style.SUCCESS('🔍 Запуск системы мониторинга...')  # type: ignore
        )

        try:
            from core.data_ingestion.monitoring import start_monitoring
            start_monitoring()
            self.stdout.write(
                self.style.SUCCESS('✅ Система мониторинга запущена')  # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при запуске мониторинга: {e}')
            )

    def stop_monitoring(self):
        """Останавливает систему мониторинга"""
        self.stdout.write(
            self.style.WARNING('🛑 Остановка системы мониторинга...')  # type: ignore
        )

        try:
            from core.data_ingestion.monitoring import stop_monitoring
            stop_monitoring()
            self.stdout.write(
                self.style.SUCCESS('✅ Система мониторинга остановлена')  # type: ignore
            )
        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при остановке мониторинга: {e}')
            )

    def show_status(self):
        """Показывает статус системы мониторинга"""
        self.stdout.write(
            self.style.SUCCESS('📊 Статус системы мониторинга')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_monitoring_service()

            # Статус сервиса
            status_icon = "🟢" if service.is_running else "🔴"
            self.stdout.write(
                f'Сервис мониторинга: {status_icon} {"Запущен" if service.is_running else "Остановлен"}')  # type: ignore

            if service.is_running:
                # Сводка уведомлений
                alerts_summary = service.get_alerts_summary()
                self.stdout.write('\n📋 Уведомления:')
                self.stdout.write(f'  Активных: {alerts_summary["total_active"]}')

                for level, count in alerts_summary['by_level'].items():
                    if count > 0:
                        level_icon = {
                            'info': 'ℹ️',
                            'warning': '⚠️',
                            'error': '❌',
                            'critical': '🚨'
                        }.get(level, '📌')
                        self.stdout.write(f'  {level_icon} {level.upper()}: {count}')

                # Последние уведомления
                if alerts_summary['recent_alerts']:
                    self.stdout.write('\n🔔 Последние уведомления:')
                    for alert in alerts_summary['recent_alerts'][-5:]:
                        timestamp = alert['timestamp'][:19].replace('T', ' ')
                        level_icon = {
                            'info': 'ℹ️',
                            'warning': '⚠️',
                            'error': '❌',
                            'critical': '🚨'
                        }.get(alert['level'], '📌')
                        self.stdout.write(
                            f'  {level_icon} [{timestamp}] {alert["title"]}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при получении статуса: {e}')  # type: ignore
            )

    def show_health(self):
        """Показывает состояние здоровья системы"""
        self.stdout.write(
            self.style.SUCCESS('🏥 Состояние здоровья системы')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_monitoring_service()
            health = service.get_health_status()

            # Общий статус
            overall_status = health['overall_status']
            status_icon = {
                'healthy': '🟢',
                'warning': '🟡',
                'critical': '🔴'
            }.get(overall_status, '⚪')

            self.stdout.write(
                f'Общее состояние: {status_icon} {overall_status.upper()}')
            self.stdout.write(f'Время проверки: {health["timestamp"]}')

            # Детали по компонентам
            self.stdout.write('\n🔧 Компоненты:')
            for check_name, check_result in health['checks'].items():
                status = check_result.get('status', 'unknown')
                status_icon = {
                    'healthy': '🟢',
                    'warning': '🟡',
                    'critical': '🔴',
                    'unknown': '⚪'
                }.get(status, '⚪')

                self.stdout.write(
                    f'  {status_icon} {check_name}: {check_result.get("message", "Нет информации")}')

                # Показываем метрики если есть
                if 'metrics' in check_result:
                    metrics = check_result['metrics']
                    if isinstance(metrics, dict):
                        for metric_name, metric_value in metrics.items():
                            if isinstance(metric_value, (int, float)):
                                self.stdout.write(
                                    f'    • {metric_name}: {metric_value}')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при получении состояния здоровья: {e}')
            )

    def show_alerts(self):
        """Показывает все уведомления"""
        self.stdout.write(
            self.style.SUCCESS('🔔 Все уведомления')  # type: ignore
        )
        self.stdout.write('=' * 60)

        try:
            service = get_monitoring_service()
            alert_manager = service.alert_manager

            # Активные уведомления
            active_alerts = alert_manager.get_active_alerts()

            if not active_alerts:
                self.stdout.write('✅ Нет активных уведомлений')
                return

            self.stdout.write(f'📋 Активных уведомлений: {len(active_alerts)}')
            self.stdout.write('')

            for alert in active_alerts:
                level_icon = {
                    AlertLevel.INFO: 'ℹ️',
                    AlertLevel.WARNING: '⚠️',
                    AlertLevel.ERROR: '❌',
                    AlertLevel.CRITICAL: '🚨'
                }.get(alert.level, '📌')

                timestamp = alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')

                self.stdout.write(
                    f'{level_icon} [{alert.level.value.upper()}] {alert.title}')
                self.stdout.write(f'   Время: {timestamp}')
                self.stdout.write(f'   Источник: {alert.source}')
                self.stdout.write(f'   Сообщение: {alert.message}')
                self.stdout.write(f'   ID: {alert.id}')
                self.stdout.write('')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при получении уведомлений: {e}')
            )

    def test_alert(self, options):
        """Создает тестовое уведомление"""
        level_str = options.get('level', 'info')

        try:
            level = AlertLevel(level_str)
        except ValueError:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Неверный уровень уведомления: {level_str}')
            )
            return

        self.stdout.write(
            self.style.SUCCESS(
                f'🧪 Создание тестового уведомления уровня {level.value}...')  # type: ignore
        )

        try:
            service = get_monitoring_service()
            alert_manager = service.alert_manager

            alert = alert_manager.create_alert(
                level=level,
                title=f"Тестовое уведомление {level.value}",
                message=f"Это тестовое уведомление для проверки системы мониторинга. Уровень: {level.value}",
                source="test")

            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Тестовое уведомление создано: {alert.id}')  # type: ignore
            )

            # Показываем детали
            self.stdout.write(f'   Уровень: {alert.level.value}')
            self.stdout.write(f'   Заголовок: {alert.title}')
            self.stdout.write(
                f'   Время: {alert.timestamp.strftime("%Y-%m-%d %H:%M:%S")}')

        except Exception as e:
            self.stdout.write(
                # type: ignore
                self.style.ERROR(f'❌ Ошибка при создании тестового уведомления: {e}')
            )
