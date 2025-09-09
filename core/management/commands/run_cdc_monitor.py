import time
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Запускает легкий CDC-мониторинг (poll каждые 24 часа или по флагу --once)"

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Однократный запуск")

    def handle(self, *args, **options):
        from core.data_ingestion.monitor import DataMonitor  # noqa: E402

        monitor = DataMonitor()
        self.stdout.write(self.style.SUCCESS("CDC монитор: старт"))  # type: ignore

        def cycle():
            try:
                monitor.run_monitoring_cycle()
                self.stdout.write(self.style.SUCCESS("CDC цикл завершен"))  # type: ignore
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"CDC ошибка: {e}"))  # type: ignore 

        if options.get("once"):
            cycle()
            return

        while True:
            cycle()
            time.sleep(60 * 60 * 24)


