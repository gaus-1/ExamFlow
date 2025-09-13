"""
Модуль Change Data Capture для мониторинга обновлений источников данных
"""

import logging
import hashlib
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import threading
from queue import Queue

from django.utils import timezone
from django.conf import settings

from core.models import FIPISourceMap
from core.data_ingestion.advanced_fipi_scraper import AdvancedFIPIScraper

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Типы изменений"""
    NEW = "new"
    UPDATED = "updated"
    DELETED = "deleted"
    NO_CHANGE = "no_change"

@dataclass
class ChangeEvent:
    """Событие изменения"""
    source_id: str
    change_type: ChangeType
    old_hash: Optional[str]
    new_hash: Optional[str]
    timestamp: datetime
    url: str
    metadata: Dict[str, Any]

class ContentHasher:
    """Генератор хешей для контента"""

    def __init__(self):
        self.scraper = AdvancedFIPIScraper()

    def get_content_hash(self, url: str) -> Optional[str]:
        """Получает хеш содержимого по URL"""
        try:
            content = self.scraper.get_page_content(url)
            if content:
                return self.scraper.get_content_hash(str(content))
            return None
        except Exception as e:
            logger.error("Ошибка получения хеша для {url}: {e}")
            return None

    def get_metadata_hash(self, source: FIPISourceMap) -> str:
        """Получает хеш метаданных источника"""
        metadata = {
            'url': source.url,
            'data_type': source.data_type,
            'subject': source.subject,
            'exam_type': source.exam_type,
            'priority': source.priority,
            'update_frequency': source.update_frequency,
            'is_active': source.is_active
        }

        metadata_str = str(sorted(metadata.items()))
        return hashlib.sha256(metadata_str.encode()).hexdigest()

class ChangeDetector:
    """Детектор изменений в источниках данных"""

    def __init__(self):
        self.hasher = ContentHasher()
        self.change_queue = Queue()
        self.detected_changes: Dict[str, ChangeEvent] = {}
        self._lock = threading.Lock()

    def detect_changes(self,
                       source_ids: Optional[List[str]] = None) -> List[ChangeEvent]:
        """Обнаруживает изменения в источниках"""
        changes = []

        try:
            # Получаем источники для проверки
            sources = self._get_sources_to_check(source_ids)

            logger.info("Проверяем изменения в {len(sources)} источниках")

            for source in sources:
                try:
                    change_event = self._check_source_changes(source)
                    if change_event and change_event.change_type != ChangeType.NO_CHANGE:
                        changes.append(change_event)
                        self._store_change_event(change_event)

                except Exception as e:
                    logger.error("Ошибка проверки источника {source.source_id}: {e}")

            logger.info("Обнаружено {len(changes)} изменений")
            return changes

        except Exception as e:
            logger.error("Ошибка обнаружения изменений: {e}")
            return []

    def _get_sources_to_check(self, source_ids: Optional[List[str]] = None):
        """Получает источники для проверки"""
        query = FIPISourceMap.objects.filter(is_active=True)  # type: ignore

        if source_ids:
            query = query.filter(source_id__in=source_ids)

        # Фильтруем по частоте обновления
        now = timezone.now()
        sources_to_check = []

        for source in query:
            if self._should_check_source(source, now):
                sources_to_check.append(source)

        return sources_to_check

    def _should_check_source(self, source: FIPISourceMap, now: datetime) -> bool:
        """Определяет, нужно ли проверять источник"""
        if not source.last_checked:
            return True

        last_checked = source.last_checked  # type: ignore
        time_since_check = now - last_checked  # type: ignore

        if source.update_frequency == 'daily':
            return time_since_check.days >= 1
        elif source.update_frequency == 'weekly':
            return time_since_check.days >= 7
        elif source.update_frequency == 'monthly':
            return time_since_check.days >= 30
        elif source.update_frequency == 'annually':
            return time_since_check.days >= 365
        elif source.update_frequency == 'on_demand':
            return False  # Проверяется только по требованию

        return True

    def _check_source_changes(self, source: FIPISourceMap) -> Optional[ChangeEvent]:
        """Проверяет изменения в конкретном источнике"""
        try:
            # Получаем текущий хеш контента
            current_hash = self.hasher.get_content_hash(str(source.url))

            if current_hash is None:
                logger.warning("Не удалось получить хеш для {source.source_id}")
                return None

            # Определяем тип изменения
            change_type = self._determine_change_type(source, current_hash)

            # Создаем событие изменения
            change_event = ChangeEvent(
                source_id=str(source.source_id),
                change_type=change_type,
                old_hash=str(source.content_hash) if source.content_hash else None,
                new_hash=current_hash,
                timestamp=timezone.now(),
                url=str(source.url),
                metadata={
                    'data_type': source.data_type,
                    'subject': source.subject,
                    'exam_type': source.exam_type,
                    'priority': source.priority
                }
            )

            # Обновляем источник
            if change_type != ChangeType.NO_CHANGE:
                source.mark_as_checked(current_hash)
                if change_type == ChangeType.UPDATED:
                    source.mark_as_updated()

            return change_event

        except Exception as e:
            logger.error("Ошибка проверки источника {source.source_id}: {e}")
            return None

    def _determine_change_type(
            self,
            source: FIPISourceMap,
            current_hash: str) -> ChangeType:
        """Определяет тип изменения"""
        if not source.content_hash:
            return ChangeType.NEW
        elif source.content_hash != current_hash:
            return ChangeType.UPDATED
        else:
            return ChangeType.NO_CHANGE

    def _store_change_event(self, change_event: ChangeEvent):
        """Сохраняет событие изменения"""
        with self._lock:
            self.detected_changes[change_event.source_id] = change_event
            self.change_queue.put(change_event)

    def get_recent_changes(self, hours: int = 24) -> List[ChangeEvent]:
        """Получает недавние изменения"""
        cutoff_time = timezone.now() - timedelta(hours=hours)

        with self._lock:
            recent_changes = [
                change for change in self.detected_changes.values()
                if change.timestamp >= cutoff_time
            ]

        return sorted(recent_changes, key=lambda x: x.timestamp, reverse=True)

    def get_change_statistics(self) -> Dict[str, Any]:
        """Получает статистику изменений"""
        with self._lock:
            total_changes = len(self.detected_changes)

            change_counts = {
                ChangeType.NEW.value: 0,
                ChangeType.UPDATED.value: 0,
                ChangeType.DELETED.value: 0
            }

            for change in self.detected_changes.values():
                change_counts[change.change_type.value] += 1

            return {
                'total_changes': total_changes,
                'change_counts': change_counts,
                'queue_size': self.change_queue.qsize()
            }

class ChangeNotificationService:
    """Сервис уведомлений об изменениях"""

    def __init__(self):
        self.notification_channels = self._setup_channels()

    def _setup_channels(self) -> Dict[str, bool]:
        """Настраивает каналы уведомлений"""
        return {
            'email': getattr(settings, 'EMAIL_BACKEND', None) is not None,
            'webhook': getattr(settings, 'CHANGE_WEBHOOK_URL', None) is not None,
            'log': True
        }

    def notify_changes(self, changes: List[ChangeEvent]):
        """Отправляет уведомления об изменениях"""
        if not changes:
            return

        # Группируем изменения по типу
        changes_by_type = {}
        for change in changes:
            change_type = change.change_type.value
            if change_type not in changes_by_type:
                changes_by_type[change_type] = []
            changes_by_type[change_type].append(change)

        # Отправляем уведомления
        for change_type, type_changes in changes_by_type.items():
            self._send_notification(change_type, type_changes)

    def _send_notification(self, change_type: str, changes: List[ChangeEvent]):
        """Отправляет уведомление о типе изменений"""
        try:
            if self.notification_channels['email']:
                self._send_email_notification(change_type, changes)

            if self.notification_channels['webhook']:
                self._send_webhook_notification(change_type, changes)

            # Логирование
            logger.info(
                "Уведомление отправлено: {change_type} - {len(changes)} изменений")

        except Exception as e:
            logger.error("Ошибка отправки уведомления: {e}")

    def _send_email_notification(self, change_type: str, changes: List[ChangeEvent]):
        """Отправляет email уведомление"""
        try:
            from django.core.mail import send_mail
            from django.template.loader import render_to_string

            subject = "[ExamFlow] Изменения в источниках данных: {change_type}"

            context = {
                'change_type': change_type,
                'changes': changes,
                'timestamp': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
                'count': len(changes)
            }

            html_message = render_to_string(
                'monitoring/change_notification.html', context)

            send_mail(
                subject=subject,
                message="Обнаружено {len(changes)} изменений типа {change_type}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=getattr(settings, 'CHANGE_NOTIFICATION_EMAILS', []),
                html_message=html_message,
                fail_silently=False
            )

        except Exception as e:
            logger.error("Ошибка отправки email уведомления: {e}")

    def _send_webhook_notification(self, change_type: str, changes: List[ChangeEvent]):
        """Отправляет webhook уведомление"""
        try:
            import requests

            webhook_url = getattr(settings, 'CHANGE_WEBHOOK_URL', None)
            if not webhook_url:
                return

            payload = {
                'change_type': change_type,
                'changes': [
                        'source_id': change.source_id,
                        'url': change.url,
                        'timestamp': change.timestamp.isoformat(),
                        'metadata': change.metadata
                    }
                    for change in changes
                ],
                'count': len(changes),
                'timestamp': timezone.now().isoformat()
            }

            response = requests.post(
                webhook_url,
                json=payload,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("Webhook уведомление отправлено: {change_type}")
            else:
                logger.warning("Webhook вернул статус {response.status_code}")

        except Exception as e:
            logger.error("Ошибка отправки webhook уведомления: {e}")

class ChangeDataCaptureService:
    """Основной сервис Change Data Capture"""

    def __init__(self):
        self.detector = ChangeDetector()
        self.notification_service = ChangeNotificationService()
        self.is_running = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self.check_interval = 3600  # 1 час

    def start(self):
        """Запускает сервис мониторинга изменений"""
        if self.is_running:
            return

        self.is_running = True
        self._monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        logger.info("Сервис Change Data Capture запущен")

    def stop(self):
        """Останавливает сервис мониторинга изменений"""
        self.is_running = False
        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5)
        logger.info("Сервис Change Data Capture остановлен")

    def _monitoring_loop(self):
        """Основной цикл мониторинга"""
        while self.is_running:
            try:
                # Обнаруживаем изменения
                changes = self.detector.detect_changes()

                # Отправляем уведомления
                if changes:
                    self.notification_service.notify_changes(changes)

                # Ждем следующую проверку
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error("Ошибка в цикле мониторинга изменений: {e}")
                time.sleep(300)  # Пауза при ошибке

    def force_check(self, source_ids: Optional[List[str]] = None) -> List[ChangeEvent]:
        """Принудительная проверка изменений"""
        return self.detector.detect_changes(source_ids)

    def get_statistics(self) -> Dict[str, Any]:
        """Получает статистику сервиса"""
        return {
            'is_running': self.is_running,
            'check_interval': self.check_interval,
            'detector_stats': self.detector.get_change_statistics(),
            'recent_changes': len(self.detector.get_recent_changes())
        }

# Глобальный экземпляр сервиса
_cdc_service: Optional[ChangeDataCaptureService] = None

def get_cdc_service() -> ChangeDataCaptureService:
    """Получает глобальный экземпляр сервиса CDC"""
    global _cdc_service
    if _cdc_service is None:
        _cdc_service = ChangeDataCaptureService()
    return _cdc_service

def start_change_monitoring():
    """Запускает мониторинг изменений"""
    service = get_cdc_service()
    service.start()
    return service

def stop_change_monitoring():
    """Останавливает мониторинг изменений"""
    global _cdc_service
    if _cdc_service:
        _cdc_service.stop()
        _cdc_service = None
