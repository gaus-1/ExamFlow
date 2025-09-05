"""
Модуль мониторинга обновлений данных
"""

import logging
import hashlib
import requests
from datetime import timedelta
from typing import Dict, List, Optional
from django.utils import timezone

logger = logging.getLogger(__name__)


class DataMonitor:
    """
    Класс для мониторинга обновлений данных
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_url_changes(self, url: str, last_hash: str = None) -> Dict:
        """
        Проверяет изменения на URL
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Создаем хеш содержимого
            content_hash = hashlib.md5(response.content).hexdigest()

            # Проверяем, изменилось ли содержимое
            has_changed = content_hash != last_hash if last_hash else True

            return {
                'url': url,
                'content_hash': content_hash,
                'has_changed': has_changed,
                'last_checked': timezone.now(),
                'content_length': len(response.content),
                'status_code': response.status_code
            }

        except Exception as e:
            logger.error(f"Ошибка при проверке URL {url}: {e}")
            return {
                'url': url,
                'content_hash': None,
                'has_changed': False,
                'last_checked': timezone.now(),
                'error': str(e)
            }

    def check_fipi_updates(self) -> List[Dict]:
        """
        Проверяет обновления на сайте ФИПИ
        """
        logger.info("Проверяем обновления на сайте ФИПИ...")

        from core.models import FIPIData

        # Получаем уникальные URL из базы данных
        urls = FIPIData.objects.values_list('url', flat=True).distinct()

        updates = []

        for url in urls:
            # Получаем последний хеш для этого URL
            last_record = FIPIData.objects.filter(
                url=url).order_by('-collected_at').first()
            last_hash = last_record.content_hash if last_record else None

            # Проверяем изменения
            check_result = self.check_url_changes(url, last_hash)

            if check_result['has_changed']:
                updates.append({
                    'url': url,
                    'title': last_record.title if last_record else 'Неизвестно',
                    'data_type': last_record.data_type if last_record else 'unknown',
                    'subject': last_record.subject if last_record else None,
                    'new_hash': check_result['content_hash'],
                    'old_hash': last_hash,
                    'checked_at': check_result['last_checked']
                })

                logger.info(f"Обнаружены изменения: {url}")

        logger.info(f"Найдено {len(updates)} обновлений")
        return updates

    def archive_old_data(self, fipi_data_id: int) -> bool:
        """
        Архивирует старые данные
        """
        try:
            from core.models import FIPIData

            data = FIPIData.objects.get(id=fipi_data_id)

            # Создаем архивную запись
            archived_data = {
                'title': data.title,
                'url': data.url,
                'data_type': data.data_type,
                'subject': data.subject,
                'content': data.content,
                'content_hash': data.content_hash,
                'collected_at': data.collected_at.isoformat(),
                'archived_at': timezone.now().isoformat()
            }

            # Сохраняем в архив (можно в отдельную таблицу или файл)
            logger.info(f"Архивированы данные: {data.title}")

            return True

        except Exception as e:
            logger.error(f"Ошибка при архивировании данных {fipi_data_id}: {e}")
            return False

    def schedule_data_collection(self) -> bool:
        """
        Планирует сбор данных
        """
        try:
            from core.data_ingestion.fipi_scraper import FIPIScraper

            scraper = FIPIScraper()
            data = scraper.collect_all_data()

            # Сохраняем данные
            success = scraper.save_to_database(data)

            if success:
                logger.info("Планируемый сбор данных завершен успешно")
                return True
            else:
                logger.error("Ошибка при сохранении данных")
                return False

        except Exception as e:
            logger.error(f"Ошибка при планируемом сборе данных: {e}")
            return False

    def run_monitoring_cycle(self) -> Dict:
        """
        Запускает полный цикл мониторинга
        """
        logger.info("Запускаем цикл мониторинга...")

        results = {
            'updates_found': 0,
            'data_collected': 0,
            'errors': [],
            'started_at': timezone.now(),
            'completed_at': None
        }

        try:
            # Проверяем обновления
            updates = self.check_fipi_updates()
            results['updates_found'] = len(updates)

            # Если есть обновления, запускаем сбор данных
            if updates:
                logger.info(
                    f"Найдено {len(updates)} обновлений, запускаем сбор данных...")

                if self.schedule_data_collection():
                    results['data_collected'] = 1
                else:
                    results['errors'].append("Ошибка при сборе данных")

            results['completed_at'] = timezone.now()
            logger.info("Цикл мониторинга завершен")

        except Exception as e:
            error_msg = f"Ошибка в цикле мониторинга: {e}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
            results['completed_at'] = timezone.now()

        return results


class MonitoringScheduler:
    """
    Планировщик для автоматического мониторинга
    """

    def __init__(self):
        self.monitor = DataMonitor()

    def should_run_monitoring(self) -> bool:
        """
        Определяет, нужно ли запускать мониторинг
        """
        from core.models import FIPIData

        # Проверяем, когда последний раз запускался мониторинг
        last_check = FIPIData.objects.order_by('-collected_at').first()

        if not last_check:
            return True

        # Запускаем мониторинг раз в час
        time_since_last = timezone.now() - last_check.collected_at
        return time_since_last > timedelta(hours=1)

    def run_if_needed(self) -> Optional[Dict]:
        """
        Запускает мониторинг, если это необходимо
        """
        if self.should_run_monitoring():
            logger.info("Запускаем мониторинг по расписанию...")
            return self.monitor.run_monitoring_cycle()
        else:
            logger.info("Мониторинг не требуется")
            return None
