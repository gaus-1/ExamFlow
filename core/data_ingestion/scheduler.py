"""
Планировщик задач для автоматического сбора данных
Использует APScheduler для периодического запуска задач сбора
"""

import logging
from typing import Dict, Optional
from datetime import timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from django.utils import timezone

from core.data_ingestion.ingestion_engine import get_ingestion_engine, TaskPriority
from core.models import FIPISourceMap

logger = logging.getLogger(__name__)


class DataIngestionScheduler:
    """Планировщик для автоматического сбора данных"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.engine = get_ingestion_engine()
        self._setup_event_listeners()
        self._setup_jobs()

    def _setup_event_listeners(self):
        """Настраивает обработчики событий планировщика"""
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )

    def _setup_jobs(self):
        """Настраивает задачи планировщика"""

        # Критически важные источники - ежедневно в 2:00
        self.scheduler.add_job(
            func=self._collect_critical_sources,
            trigger=CronTrigger(hour=2, minute=0),
            id='collect_critical_sources',
            name='Сбор критически важных источников',
            replace_existing=True
        )

        # Высокоприоритетные источники - каждые 6 часов
        self.scheduler.add_job(
            func=self._collect_high_priority_sources,
            trigger=IntervalTrigger(hours=6),
            id='collect_high_priority_sources',
            name='Сбор высокоприоритетных источников',
            replace_existing=True
        )

        # Среднеприоритетные источники - ежедневно в 4:00
        self.scheduler.add_job(
            func=self._collect_medium_priority_sources,
            trigger=CronTrigger(hour=4, minute=0),
            id='collect_medium_priority_sources',
            name='Сбор среднеприоритетных источников',
            replace_existing=True
        )

        # Низкоприоритетные источники - еженедельно в воскресенье в 6:00
        self.scheduler.add_job(
            func=self._collect_low_priority_sources,
            trigger=CronTrigger(day_of_week=6, hour=6, minute=0),  # Воскресенье
            id='collect_low_priority_sources',
            name='Сбор низкоприоритетных источников',
            replace_existing=True
        )

        # Мониторинг обновлений - каждые 30 минут
        self.scheduler.add_job(
            func=self._monitor_updates,
            trigger=IntervalTrigger(minutes=30),
            id='monitor_updates',
            name='Мониторинг обновлений',
            replace_existing=True
        )

        # Очистка старых данных - еженедельно в понедельник в 3:00
        self.scheduler.add_job(
            func=self._cleanup_old_data,
            trigger=CronTrigger(day_of_week=0, hour=3, minute=0),  # Понедельник
            id='cleanup_old_data',
            name='Очистка старых данных',
            replace_existing=True
        )

        # Статистика и отчеты - ежедневно в 8:00
        self.scheduler.add_job(
            func=self._generate_daily_report,
            trigger=CronTrigger(hour=8, minute=0),
            id='generate_daily_report',
            name='Генерация ежедневного отчета',
            replace_existing=True
        )

    def start(self):
        """Запускает планировщик"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("Планировщик сбора данных запущен")

            # Запускаем движок сбора данных
            self.engine.start()
        else:
            logger.warning("Планировщик уже запущен")

    def stop(self):
        """Останавливает планировщик"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Планировщик сбора данных остановлен")

            # Останавливаем движок
            self.engine.stop()
        else:
            logger.warning("Планировщик не запущен")

    def _collect_critical_sources(self):
        """Собирает критически важные источники"""
        logger.info("Начинаем сбор критически важных источников")
        try:
            count = self.engine.add_source_tasks(priority_filter=TaskPriority.CRITICAL)
            logger.info(f"Добавлено {count} задач для критически важных источников")
        except Exception as e:
            logger.error(f"Ошибка при сборе критически важных источников: {e}")

    def _collect_high_priority_sources(self):
        """Собирает высокоприоритетные источники"""
        logger.info("Начинаем сбор высокоприоритетных источников")
        try:
            count = self.engine.add_source_tasks(priority_filter=TaskPriority.HIGH)
            logger.info(f"Добавлено {count} задач для высокоприоритетных источников")
        except Exception as e:
            logger.error(f"Ошибка при сборе высокоприоритетных источников: {e}")

    def _collect_medium_priority_sources(self):
        """Собирает среднеприоритетные источники"""
        logger.info("Начинаем сбор среднеприоритетных источников")
        try:
            count = self.engine.add_source_tasks(priority_filter=TaskPriority.MEDIUM)
            logger.info(f"Добавлено {count} задач для среднеприоритетных источников")
        except Exception as e:
            logger.error(f"Ошибка при сборе среднеприоритетных источников: {e}")

    def _collect_low_priority_sources(self):
        """Собирает низкоприоритетные источники"""
        logger.info("Начинаем сбор низкоприоритетных источников")
        try:
            count = self.engine.add_source_tasks(priority_filter=TaskPriority.LOW)
            logger.info(f"Добавлено {count} задач для низкоприоритетных источников")
        except Exception as e:
            logger.error(f"Ошибка при сборе низкоприоритетных источников: {e}")

    def _monitor_updates(self):
        """Мониторит обновления источников"""
        logger.debug("Мониторинг обновлений источников")
        try:
            # Проверяем источники, которые нуждаются в обновлении
            sources_needing_update = FIPISourceMap.objects.filter(  # type: ignore
                is_active=True
            ).exclude(
                last_checked__isnull=True
            )

            update_count = 0
            for source in sources_needing_update:
                if source.needs_update():
                    update_count += 1

            if update_count > 0:
                logger.info(f"Найдено {update_count} источников, требующих обновления")
                # Добавляем задачи для обновления
                self.engine.add_source_tasks()

        except Exception as e:
            logger.error(f"Ошибка при мониторинге обновлений: {e}")

    def _cleanup_old_data(self):
        """Очищает старые данные"""
        logger.info("Начинаем очистку старых данных")
        try:
            from core.models import FIPIData

            # Удаляем данные старше 1 года
            cutoff_date = timezone.now() - timedelta(days=365)
            old_data = FIPIData.objects.filter(  # type: ignore
                collected_at__lt=cutoff_date,
                is_processed=True
            )

            count = old_data.count()
            old_data.delete()

            logger.info(f"Удалено {count} старых записей данных")

        except Exception as e:
            logger.error(f"Ошибка при очистке старых данных: {e}")

    def _generate_daily_report(self):
        """Генерирует ежедневный отчет"""
        logger.info("Генерация ежедневного отчета")
        try:
            from core.models import FIPIData

            # Статистика за последние 24 часа
            yesterday = timezone.now() - timedelta(days=1)

            stats = {
                'date': timezone.now().date().isoformat(),
                # type: ignore
                'sources_total': FIPISourceMap.objects.filter(is_active=True).count(),
                'sources_updated_today': FIPISourceMap.objects.filter(  # type: ignore
                    is_active=True,
                    last_checked__gte=yesterday
                ).count(),
                'data_collected_today': FIPIData.objects.filter(  # type: ignore
                    collected_at__gte=yesterday
                ).count(),
                'data_processed_today': FIPIData.objects.filter(  # type: ignore
                    processed_at__gte=yesterday
                ).count(),
                'engine_stats': self.engine.get_statistics()
            }

            logger.info(f"Ежедневный отчет: {stats}")

            # Здесь можно добавить отправку отчета по email или в систему мониторинга

        except Exception as e:
            logger.error(f"Ошибка при генерации ежедневного отчета: {e}")

    def _job_executed_listener(self, event):
        """Обработчик событий выполнения задач"""
        if event.exception:
            logger.error(f"Ошибка в задаче {event.job_id}: {event.exception}")
        else:
            logger.info(f"Задача {event.job_id} выполнена успешно")

    def get_job_status(self) -> Dict:
        """Получает статус всех задач"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })

        return {
            'scheduler_running': self.scheduler.running,
            'jobs': jobs,
            'engine_stats': self.engine.get_statistics()
        }

    def trigger_job(self, job_id: str) -> bool:
        """Принудительно запускает задачу"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=timezone.now())
                logger.info(f"Задача {job_id} запланирована на немедленное выполнение")
                return True
            else:
                logger.error(f"Задача {job_id} не найдена")
                return False
        except Exception as e:
            logger.error(f"Ошибка при запуске задачи {job_id}: {e}")
            return False


# Глобальный экземпляр планировщика
_scheduler: Optional[DataIngestionScheduler] = None


def get_scheduler() -> DataIngestionScheduler:
    """Получает глобальный экземпляр планировщика"""
    global _scheduler
    if _scheduler is None:
        _scheduler = DataIngestionScheduler()
    return _scheduler


def start_scheduler():
    """Запускает планировщик"""
    scheduler = get_scheduler()
    scheduler.start()
    return scheduler


def stop_scheduler():
    """Останавливает планировщик"""
    global _scheduler
    if _scheduler:
        _scheduler.stop()
        _scheduler = None
