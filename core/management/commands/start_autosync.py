"""
Запуск автоматического сбора и обработки данных (автосинхронизация)
- Планировщик APScheduler поднимается внутри Django management-команды
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Optional

from django.core.management.base import BaseCommand
from django.utils import timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from core.models import FIPISourceMap, FIPIData
from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper
from core.data_ingestion.ingestion_engine import IngestionEngine, TaskPriority
# Импорт PDF-процессора переносим внутрь функции, чтобы не падать на окружениях без cffi/cryptography

logger = logging.getLogger(__name__)


def _send_telegram_broadcast(text: str) -> None:
    """Простое уведомление в Telegram (опционально).
    Требует TELEGRAM_BOT_TOKEN и TELEGRAM_BROADCAST_CHAT_ID в окружении.
    """
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('TELEGRAM_BROADCAST_CHAT_ID')
    if not token or not chat_id:
        return
    try:
        import requests
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, data={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML'
        }, timeout=10)
    except Exception as e:
        logger.warning(f"Не удалось отправить Telegram-уведомление: {e}")


class Command(BaseCommand):
    help = "Запускает фоновый планировщик для автосбора данных и обработки"

    def add_arguments(self, parser):
        parser.add_argument('--ingest-interval-min', type=int, default=120,
                            help='Периодичность добавления задач IngestionEngine, мин')
        parser.add_argument('--scrape-interval-min', type=int, default=180,
                            help='Периодичность прохода AdvancedFIPIScraper, мин')
        parser.add_argument('--pdf-interval-min', type=int, default=360,
                            help='Периодичность обработки PDF, мин')
        parser.add_argument('--detect-interval-min', type=int, default=360,
                            help='Периодичность проверки изменений источников, мин')
        parser.add_argument('--pdf-batch', type=int, default=20,
                            help='Сколько PDF обрабатывать за цикл')

    def handle(self, *args, **options):
        ingest_interval_min: int = options['ingest_interval_min']
        scrape_interval_min: int = options['scrape_interval_min']
        pdf_interval_min: int = options['pdf_interval_min']
        detect_interval_min: int = options['detect_interval_min']
        pdf_batch: int = options['pdf_batch']

        self.stdout.write(self.style.SUCCESS('🚀 Старт автосинхронизации'))  # type: ignore

        scheduler = BackgroundScheduler(timezone=str(timezone.get_current_timezone()))

        # 1) Периодически добавляем задачи в IngestionEngine из активных источников
        def add_ingestion_tasks():
            try:
                engine = IngestionEngine()
                if not engine.is_running:
                    engine.start()
                active = FIPISourceMap.objects.filter(is_active=True)  # type: ignore
                added = 0
                now_ts = int(time.time())
                for src in active:
                    from core.data_ingestion.ingestion_engine import IngestionTask
                    task = IngestionTask(
                        id=f"task_{src.source_id}_{now_ts}",
                        source_id=src.source_id,
                        url=src.url,
                        priority=TaskPriority.HIGH,
                        data_type=src.data_type,
                        created_at=timezone.now()
                    )
                    engine.task_queue.add_task(task)
                    added += 1
                logger.info(f"Автосинхро: добавлено задач в IngestionEngine: {added}")
            except Exception as e:
                logger.error(f"Ошибка add_ingestion_tasks: {e}")

        scheduler.add_job(add_ingestion_tasks,
                          trigger=IntervalTrigger(minutes=ingest_interval_min),
                          id='add_ingestion_tasks', max_instances=1, coalesce=True, replace_existing=True)

        # 2) Периодический проход скрейпера по индекс-страницам c сохранением в БД
        def run_scraper_cycle():
            try:
                scraper = AdvancedFIPIScraper()
                data = scraper.collect_from_source_map()
                scraper.save_to_database(data)
                logger.info("Автосинхро: цикл скрейпера выполнен")
            except Exception as e:
                logger.error(f"Ошибка run_scraper_cycle: {e}")

        scheduler.add_job(run_scraper_cycle,
                          trigger=IntervalTrigger(minutes=scrape_interval_min),
                          id='run_scraper_cycle', max_instances=1, coalesce=True, replace_existing=True)

        # 3) Периодическая обработка PDF
        def process_pdfs():
            try:
                # Флаг для явного разрешения PDF-пайплайна (по умолчанию выключен для совместимости с Windows локально)
                if os.getenv('USE_PDF_PIPELINE', '0') != '1':
                    logger.info("Автосинхро: PDF-пайплайн отключен (USE_PDF_PIPELINE!=1)")
                    return

                # Ленивая загрузка, чтобы не импортировать при старте команды
                from core.data_ingestion.pdf_processor import get_pdf_processor  # type: ignore
                processor = get_pdf_processor()
                pdf_qs = FIPIData.objects.filter(  # type: ignore
                    is_processed=False,
                    url__iendswith='.pdf',
                ).order_by('id')[:pdf_batch]

                done = 0
                for item in pdf_qs:
                    result = processor.process_pdf(item)
                    if isinstance(result, dict) and result.get('status') == 'completed':
                        done += 1
                logger.info(f"Автосинхро: PDF обработано {done}/{len(pdf_qs)}")
            except Exception as e:
                logger.error(f"Ошибка process_pdfs: {e}")

        scheduler.add_job(process_pdfs,
                          trigger=IntervalTrigger(minutes=pdf_interval_min),
                          id='process_pdfs', max_instances=1, coalesce=True, replace_existing=True)

        # 4) Периодическая проверка изменений источников и уведомление в бот
        def detect_changes_and_notify():
            try:
                # Простейшая эвристика: сообщаем о новых записях за последние 6 часов
                since = timezone.now() - timedelta(hours=6)
                new_count = FIPIData.objects.filter(created_at__gte=since).count()  # type: ignore
                if new_count > 0:
                    _send_telegram_broadcast(
                        f"📥 Обновление контента: добавлено {new_count} материалов за последние 6 часов"
                    )
                logger.info("Автосинхро: проверка изменений/уведомлений завершена")
            except Exception as e:
                logger.error(f"Ошибка detect_changes_and_notify: {e}")

        scheduler.add_job(detect_changes_and_notify,
                          trigger=IntervalTrigger(minutes=detect_interval_min),
                          id='detect_changes_and_notify', max_instances=1, coalesce=True, replace_existing=True)

        scheduler.start()
        self.stdout.write(self.style.SUCCESS('✅ Планировщик запущен (Ctrl+C для остановки)'))  # type: ignore

        try:
            while True:
                time.sleep(5)
        except KeyboardInterrupt:
            self.stdout.write(self.style.WARNING('Остановка планировщика...'))  # type: ignore
            scheduler.shutdown(wait=False)
            self.stdout.write(self.style.SUCCESS('Готово'))  # type: ignore


