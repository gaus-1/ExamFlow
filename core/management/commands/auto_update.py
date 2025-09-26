"""
Команда Django для управления системой автообновлений
"""

import signal
import sys
import time

from django.core.management.base import BaseCommand

from core.auto_updater import auto_updater, start_auto_updater, stop_auto_updater


class Command(BaseCommand):
    help = "Управление системой автоматических обновлений материалов ФИПИ"

    def add_arguments(self, parser):
        parser.add_argument(
            "action",
            choices=["start", "stop", "status", "manual"],
            help="Действие: start, stop, status или manual",
        )
        parser.add_argument(
            "--daemon",
            action="store_true",
            help="Запустить в фоновом режиме",
        )

    def handle(self, *args, **options):
        action = options["action"]

        if action == "start":
            self.start_service(options.get("daemon", False))
        elif action == "stop":
            self.stop_service()
        elif action == "status":
            self.show_status()
        elif action == "manual":
            self.manual_update()

    def start_service(self, daemon=False):
        """Запускает службу автообновлений"""
        self.stdout.write(self.style.SUCCESS("🚀 Запуск системы автообновлений..."))

        # Настраиваем обработчик сигналов для корректного завершения
        def signal_handler(signum, frame):
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Получен сигнал завершения. Останавливаем службу..."
                )
            )
            stop_auto_updater()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        try:
            start_auto_updater()

            self.stdout.write(self.style.SUCCESS("✅ Система автообновлений запущена!"))
            self.stdout.write(self.style.SUCCESS("📅 Расписание:"))
            self.stdout.write("  • Ежедневно в 03:00 - обновление материалов")
            self.stdout.write(
                "  • Еженедельно в воскресенье в 02:00 - полное обновление"
            )
            self.stdout.write("  • Ежедневно в 04:00 - генерация голосов")
            self.stdout.write("  • Каждые 30 минут - очистка старых данных")
            self.stdout.write(self.style.WARNING("📝 Нажмите Ctrl+C для остановки"))

            if daemon:
                # В демон-режиме просто держим процесс
                while auto_updater.is_running:
                    time.sleep(60)
            else:
                # В интерактивном режиме показываем статус
                self.run_interactive_mode()

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\n⚠️  Остановка по запросу пользователя...")
            )
            stop_auto_updater()
        except Exception:
            self.stdout.write(self.style.ERROR("❌ Ошибка запуска: {str(e)}"))

    def stop_service(self):
        """Останавливает службу автообновлений"""
        self.stdout.write("🛑 Остановка системы автообновлений...")
        stop_auto_updater()
        self.stdout.write(self.style.SUCCESS("✅ Система остановлена"))

    def show_status(self):
        """Показывает статус системы"""
        if auto_updater.is_running:
            self.stdout.write(self.style.SUCCESS("🟢 Система автообновлений активна"))
            self.stdout.write("📅 Активные задачи:")

            import schedule

            jobs = schedule.jobs
            if jobs:
                for job in jobs:
                    next_run = (
                        job.next_run.strftime("%d.%m.%Y %H:%M")
                        if job.next_run
                        else "Не запланировано"
                    )
                    self.stdout.write("  • {job.job_func.__name__}: {next_run}")
            else:
                self.stdout.write("  Нет запланированных задач")
        else:
            self.stdout.write(
                self.style.WARNING("🔴 Система автообновлений остановлена")
            )

    def manual_update(self):
        """Запускает ручное обновление"""
        self.stdout.write(
            self.style.SUCCESS("🔄 Запуск ручного обновления материалов...")
        )

        try:
            result = auto_updater.manual_update()

            self.stdout.write(self.style.SUCCESS("✅ Ручное обновление завершено!"))
            self.stdout.write(self.style.SUCCESS("📊 Результаты:"))
            self.stdout.write('  • Предметов создано: {result["subjects"]}')
            self.stdout.write('  • Заданий загружено: {result["tasks"]}')
            self.stdout.write('  • Примеров добавлено: {result["samples"]}')

        except Exception:
            self.stdout.write(
                self.style.ERROR("❌ Ошибка ручного обновления: {str(e)}")
            )

    def run_interactive_mode(self):
        """Запускает интерактивный режим с отображением статуса"""
        try:
            while auto_updater.is_running:
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("🤖 ExamFlow Auto-Updater Service")
                self.stdout.write("=" * 60)
                self.stdout.write("🟢 Статус: Активен")

                import schedule

                jobs = schedule.jobs
                self.stdout.write("📅 Запланированных задач: {len(jobs)}")

                if jobs:
                    self.stdout.write("⏰ Следующие запуски:")
                    for job in jobs[:3]:  # Показываем только 3 ближайшие
                        if job.next_run:
                            next_run = job.next_run.strftime("%d.%m %H:%M")
                            self.stdout.write("  • {job.job_func.__name__}: {next_run}")

                self.stdout.write("📝 Нажмите Ctrl+C для остановки")
                self.stdout.write("=" * 60)

                # Ждем 60 секунд перед следующим обновлением
                time.sleep(60)

        except KeyboardInterrupt:
            pass
