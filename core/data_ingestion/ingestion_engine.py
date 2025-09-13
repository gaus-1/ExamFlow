"""
Промышленный модуль сбора данных (Ingestion Engine)
Асинхронная система с очередями задач для масштабируемого сбора данных с fipi.ru
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import json
import time
import threading
from queue import Queue, Empty
import signal
import sys

from django.utils import timezone
from django.db import transaction

from core.models import FIPISourceMap, FIPIData  # type: ignore
from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper

logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Статусы задач"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    """Приоритеты задач"""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4

@dataclass
class IngestionTask:
    """Задача для сбора данных"""
    id: str
    source_id: str
    url: str
    data_type: str
    priority: TaskPriority
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = None  # type: ignore
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    error_message: Optional[str] = None
    result_data: Optional[Dict] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = timezone.now()

    def to_dict(self) -> Dict:
        """Преобразует задачу в словарь для сериализации"""
        data = asdict(self)
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['started_at'] = self.started_at.isoformat() if self.started_at else None
        data['completed_at'] = self.completed_at.isoformat() if self.completed_at else None
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'IngestionTask':
        """Создает задачу из словаря"""
        data['priority'] = TaskPriority(data['priority'])
        data['status'] = TaskStatus(data['status'])
        if data['created_at']:
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if data['started_at']:
            data['started_at'] = datetime.fromisoformat(data['started_at'])
        if data['completed_at']:
            data['completed_at'] = datetime.fromisoformat(data['completed_at'])
        return cls(**data)

class TaskQueue:
    """Очередь задач с приоритетами"""

    def __init__(self):
        self._queues = {
            TaskPriority.CRITICAL: Queue(),
            TaskPriority.HIGH: Queue(),
            TaskPriority.MEDIUM: Queue(),
            TaskPriority.LOW: Queue(),
        }
        self._task_registry: Dict[str, IngestionTask] = {}
        self._lock = threading.Lock()

    def add_task(self, task: IngestionTask):
        """Добавляет задачу в очередь"""
        with self._lock:
            self._task_registry[task.id] = task
            self._queues[task.priority].put(task)
            logger.info(
                "Задача {task.id} добавлена в очередь с приоритетом {task.priority.name}")

    def get_next_task(self) -> Optional[IngestionTask]:
        """Получает следующую задачу по приоритету"""
        with self._lock:
            # Проверяем очереди по приоритету
            for priority in [
                    TaskPriority.CRITICAL,
                    TaskPriority.HIGH,
                    TaskPriority.MEDIUM,
                    TaskPriority.LOW]:
                try:
                    task = self._queues[priority].get_nowait()
                    return task
                except Empty:
                    continue
            return None

    def get_task(self, task_id: str) -> Optional[IngestionTask]:
        """Получает задачу по ID"""
        with self._lock:
            return self._task_registry.get(task_id)

    def update_task(self, task: IngestionTask):
        """Обновляет задачу в реестре"""
        with self._lock:
            self._task_registry[task.id] = task

    def get_queue_stats(self) -> Dict:
        """Получает статистику очередей"""
        with self._lock:
            stats = {}
            for priority, queue in self._queues.items():
                stats[priority.name] = queue.qsize()
            return stats

class IngestionWorker:
    """Воркер для выполнения задач сбора данных"""

    def __init__(self, worker_id: str, task_queue: TaskQueue):
        self.worker_id = worker_id
        self.task_queue = task_queue
        self.scraper = AdvancedFIPIScraper()
        self.is_running = False
        self.current_task: Optional[IngestionTask] = None
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Запускает воркер"""
        if self.is_running:
            return

        self.is_running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()
        logger.info("Воркер {self.worker_id} запущен")

    def stop(self):
        """Останавливает воркер"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("Воркер {self.worker_id} остановлен")

    def _worker_loop(self):
        """Основной цикл воркера"""
        while self.is_running:
            try:
                task = self.task_queue.get_next_task()
                if task is None:
                    time.sleep(1)  # Нет задач, ждем
                    continue

                self._execute_task(task)

            except Exception as e:
                logger.error("Ошибка в воркере {self.worker_id}: {e}")
                time.sleep(5)  # Пауза при ошибке

    def _execute_task(self, task: IngestionTask):
        """Выполняет задачу"""
        self.current_task = task
        task.status = TaskStatus.RUNNING
        task.started_at = timezone.now()
        self.task_queue.update_task(task)

        logger.info("Воркер {self.worker_id} выполняет задачу {task.id}")

        try:
            # Получаем содержимое страницы
            content = self.scraper.get_page_content(task.url)

            if content is None:
                raise Exception("Не удалось получить содержимое для {task.url}")

            # Создаем хеш содержимого
            content_hash = self.scraper.get_content_hash(str(content))

            # Проверяем, изменилось ли содержимое
            source = FIPISourceMap.objects.get(source_id=task.source_id)  # type: ignore
            if source.content_hash == content_hash:
                logger.info("Содержимое не изменилось для {task.source_id}")
                task.status = TaskStatus.COMPLETED
                task.result_data = {
                    'status': 'no_changes',
                    'content_hash': content_hash}
            else:
                # Содержимое изменилось, сохраняем данные
                result = self._save_data(task, content, content_hash)
                task.result_data = result
                task.status = TaskStatus.COMPLETED

                # Обновляем источник
                source.mark_as_checked(content_hash)

            task.completed_at = timezone.now()
            logger.info("Задача {task.id} выполнена успешно")

        except Exception as e:
            logger.error("Ошибка при выполнении задачи {task.id}: {e}")
            task.error_message = str(e)
            task.retry_count += 1

            if task.retry_count < task.max_retries:
                task.status = TaskStatus.RETRYING
                # Возвращаем задачу в очередь для повтора
                self.task_queue.add_task(task)
                logger.info(
                    "Задача {task.id} будет повторена (попытка {task.retry_count}/{task.max_retries})")
            else:
                task.status = TaskStatus.FAILED
                logger.error(
                    "Задача {task.id} провалена после {task.max_retries} попыток")

        finally:
            self.task_queue.update_task(task)
            self.current_task = None

    def _save_data(self, task: IngestionTask, content: str, content_hash: str) -> Dict:
        """Сохраняет данные в базу"""
        try:
            with transaction.atomic():  # type: ignore
                # Проверяем, есть ли уже такая запись
                if FIPIData.objects.filter(  # type: ignore
                        content_hash=content_hash).exists():  # type: ignore
                    return {'status': 'already_exists', 'content_hash': content_hash}

                # Создаем новую запись
                fipi_data = FIPIData.objects.create(  # type: ignore
                    title=f"Данные из {task.source_id}",
                    url=task.url,
                    data_type=task.data_type,
                    content_hash=content_hash,
                    content=str(content)[:50000],  # Ограничиваем размер
                    collected_at=timezone.now()
                )

                return {
                    'status': 'saved',
                    'fipi_data_id': fipi_data.id,
                    'content_hash': content_hash,
                    'content_size': len(content)
                }

        except Exception as e:
            logger.error("Ошибка при сохранении данных для задачи {task.id}: {e}")
            raise

class IngestionEngine:
    """Основной движок сбора данных"""

    def __init__(self, max_workers: int = 5):
        self.max_workers = max_workers
        self.task_queue = TaskQueue()
        self.workers: List[IngestionWorker] = []
        self.is_running = False
        self._monitoring_thread: Optional[threading.Thread] = None

        # Настройка обработки сигналов для graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def start(self):
        """Запускает движок сбора данных"""
        if self.is_running:
            logger.warning("Движок уже запущен")
            return

        logger.info("Запуск движка сбора данных с {self.max_workers} воркерами")

        # Создаем и запускаем воркеры
        for i in range(self.max_workers):
            worker = IngestionWorker("worker-{i+1}", self.task_queue)
            worker.start()
            self.workers.append(worker)

        # Запускаем мониторинг
        self.is_running = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()

        logger.info("Движок сбора данных запущен")

    def stop(self):
        """Останавливает движок"""
        if not self.is_running:
            return

        logger.info("Остановка движка сбора данных...")
        self.is_running = False

        # Останавливаем воркеры
        for worker in self.workers:
            worker.stop()

        # Ждем завершения мониторинга
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)

        logger.info("Движок сбора данных остановлен")

    def add_source_tasks(self,
                         source_ids: Optional[List[str]] = None,
                         priority_filter: Optional[TaskPriority] = None):
        """Добавляет задачи для источников"""
        try:
            # Получаем источники
            sources_query = FIPISourceMap.objects.filter(is_active=True)  # type: ignore

            if source_ids:
                sources_query = sources_query.filter(source_id__in=source_ids)

            if priority_filter:
                sources_query = sources_query.filter(priority=priority_filter.value)

            sources = sources_query.all()

            added_count = 0
            for source in sources:
                # Проверяем, нуждается ли источник в обновлении
                if not source.needs_update():
                    continue

                # Создаем задачу
                task_id = "{source.source_id}_{int(time.time())}"
                priority = TaskPriority(source.priority)

                task = IngestionTask(
                    id=task_id,
                    source_id=source.source_id,
                    url=source.url,
                    data_type=source.data_type,
                    priority=priority
                )

                self.task_queue.add_task(task)
                added_count += 1

            logger.info("Добавлено {added_count} задач в очередь")
            return added_count

        except Exception as e:
            logger.error("Ошибка при добавлении задач: {e}")
            return 0

    def get_statistics(self) -> Dict:
        """Получает статистику движка"""
        queue_stats = self.task_queue.get_queue_stats()

        # Статистика воркеров
        worker_stats = []
        for worker in self.workers:
            worker_stats.append({
                'worker_id': worker.worker_id,
                'is_running': worker.is_running,
                'current_task': worker.current_task.id if worker.current_task else None
            })

        # Статистика задач
        all_tasks = list(self.task_queue._task_registry.values())
        task_stats = {
            'total': len(all_tasks),
            'by_status': {},
            'by_priority': {}
        }

        for task in all_tasks:
            status = task.status.value
            priority = task.priority.name

            task_stats['by_status'][status] = task_stats['by_status'].get(status, 0) + 1
            task_stats['by_priority'][priority] = task_stats['by_priority'].get(
                priority, 0) + 1

        return {
            'is_running': self.is_running,
            'queue_stats': queue_stats,
            'worker_stats': worker_stats,
            'task_stats': task_stats
        }

    def _monitoring_loop(self):
        """Цикл мониторинга"""
        while self.is_running:
            try:
                # Логируем статистику каждые 30 секунд
                stats = self.get_statistics()
                logger.info(
                    "Статистика движка: {json.dumps(stats, indent=2, default=str)}")

                time.sleep(30)

            except Exception as e:
                logger.error("Ошибка в мониторинге: {e}")
                time.sleep(10)

    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        logger.info("Получен сигнал {signum}, останавливаем движок...")
        self.stop()
        sys.exit(0)

# Глобальный экземпляр движка
_ingestion_engine: Optional[IngestionEngine] = None

def get_ingestion_engine() -> IngestionEngine:
    """Получает глобальный экземпляр движка"""
    global _ingestion_engine
    if _ingestion_engine is None:
        _ingestion_engine = IngestionEngine()
    return _ingestion_engine

def start_ingestion_engine():
    """Запускает движок сбора данных"""
    engine = get_ingestion_engine()
    engine.start()
    return engine

def stop_ingestion_engine():
    """Останавливает движок сбора данных"""
    global _ingestion_engine
    if _ingestion_engine:
        _ingestion_engine.stop()
        _ingestion_engine = None
