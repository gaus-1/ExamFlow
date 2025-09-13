"""
Система мониторинга изменений на ФИПИ
Автоматическое отслеживание обновлений для математики и русского языка
"""

import requests
import hashlib
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.utils import timezone
from django.core.mail import send_mail
from .models import FIPIData

logger = logging.getLogger(__name__)

class FIPIMonitor:
    """Монитор изменений на сайте ФИПИ"""

    def __init__(self):
        self.base_url = "https://fipi.ru"
        self.check_interval = 3600  # 1 час
        self.subjects = ['Математика', 'Русский язык']
        self.exam_types = ['ЕГЭ', 'ОГЭ']

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # URL для мониторинга
        self.monitor_urls = {
            'demo_variants': "{self.base_url}/ege/demoversii-specifikacii-kodifikatory",
            'open_bank': "{self.base_url}/ege/otkrytyy-bank-zadaniy-ege",
            'oge_demo': "{self.base_url}/oge/demoversii-specifikacii-kodifikatory",
            'oge_bank': "{self.base_url}/oge/otkrytyy-bank-zadaniy-oge"}

    def check_for_updates(self) -> Dict[str, Any]:
        """Проверяет обновления на ФИПИ"""

        logger.info("Начинаем проверку обновлений ФИПИ")

        updates = {
            'timestamp': timezone.now().isoformat(),
            'math_updates': [],
            'russian_updates': [],
            'total_updates': 0
        }

        try:
            # Проверяем демо-варианты
            demo_updates = self._check_demo_variants()
            updates['math_updates'].extend(demo_updates.get('math', []))
            updates['russian_updates'].extend(demo_updates.get('russian', []))

            # Проверяем открытый банк
            bank_updates = self._check_open_bank()
            updates['math_updates'].extend(bank_updates.get('math', []))
            updates['russian_updates'].extend(bank_updates.get('russian', []))

            # Подсчитываем общее количество обновлений
            updates['total_updates'] = (
                len(updates['math_updates']) +
                len(updates['russian_updates'])
            )

            # Если есть обновления, уведомляем администратора
            if updates['total_updates'] > 0:
                self._notify_admin(updates)
                self._save_updates_to_db(updates)

            logger.info(
                "Проверка завершена. Найдено обновлений: {updates['total_updates']}")

        except Exception as e:
            logger.error("Ошибка при проверке обновлений ФИПИ: {e}")
            updates['error'] = str(e)

        return updates

    def _check_demo_variants(self) -> Dict[str, List[Dict]]:
        """Проверяет демонстрационные варианты"""

        updates = {'math': [], 'russian': []}

        try:
            response = requests.get(
                self.monitor_urls['demo_variants'],
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()

            content = response.text
            content_hash = hashlib.md5(content.encode()).hexdigest()

            # Проверяем, изменился ли контент
            last_hash = self._get_last_content_hash('demo_variants')

            if content_hash != last_hash:
                logger.info("Обнаружены изменения в демо-вариантах")

                # Анализируем изменения для каждого предмета
                for subject in self.subjects:
                    subject_updates = self._analyze_demo_changes(content, subject)
                    if subject_updates:
                        updates[subject.lower().replace(
                            ' ', '_')].extend(subject_updates)

                # Сохраняем новый хеш
                self._save_content_hash('demo_variants', content_hash)

        except Exception as e:
            logger.error("Ошибка при проверке демо-вариантов: {e}")

        return updates

    def _check_open_bank(self) -> Dict[str, List[Dict]]:
        """Проверяет открытый банк заданий"""

        updates = {'math': [], 'russian': []}

        try:
            # Проверяем ЕГЭ
            ege_response = requests.get(
                self.monitor_urls['open_bank'],
                headers=self.headers,
                timeout=30
            )
            ege_response.raise_for_status()

            ege_content = ege_response.text
            ege_hash = hashlib.md5(ege_content.encode()).hexdigest()

            last_ege_hash = self._get_last_content_hash('open_bank_ege')

            if ege_hash != last_ege_hash:
                logger.info("Обнаружены изменения в открытом банке ЕГЭ")

                for subject in self.subjects:
                    subject_updates = self._analyze_bank_changes(
                        ege_content, subject, 'ЕГЭ')
                    if subject_updates:
                        updates[subject.lower().replace(
                            ' ', '_')].extend(subject_updates)

                self._save_content_hash('open_bank_ege', ege_hash)

            # Проверяем ОГЭ
            oge_response = requests.get(
                self.monitor_urls['oge_bank'],
                headers=self.headers,
                timeout=30
            )
            oge_response.raise_for_status()

            oge_content = oge_response.text
            oge_hash = hashlib.md5(oge_content.encode()).hexdigest()

            last_oge_hash = self._get_last_content_hash('open_bank_oge')

            if oge_hash != last_oge_hash:
                logger.info("Обнаружены изменения в открытом банке ОГЭ")

                for subject in self.subjects:
                    subject_updates = self._analyze_bank_changes(
                        oge_content, subject, 'ОГЭ')
                    if subject_updates:
                        updates[subject.lower().replace(
                            ' ', '_')].extend(subject_updates)

                self._save_content_hash('open_bank_oge', oge_hash)

        except Exception as e:
            logger.error("Ошибка при проверке открытого банка: {e}")

        return updates

    def _analyze_demo_changes(self, content: str, subject: str) -> List[Dict]:
        """Анализирует изменения в демо-вариантах"""

        updates = []

        # Ищем упоминания предмета в контенте
        subject_keywords = {
            'Математика': ['математика', 'матем', 'math'],
            'Русский язык': ['русский', 'язык', 'russian']
        }

        keywords = subject_keywords.get(subject, [])

        for keyword in keywords:
            if keyword.lower() in content.lower():
                # Ищем ссылки на файлы
                import re
                file_links = re.findall(r'href="([^"]*\.pdf[^"]*)"', content)

                for link in file_links:
                    if keyword.lower() in link.lower():
                        updates.append({
                            'type': 'demo_variant',
                            'subject': subject,
                            'url': "{self.base_url}{link}",
                            'title': "Новый демо-вариант {subject}",
                            'timestamp': timezone.now().isoformat()
                        })

        return updates

    def _analyze_bank_changes(
            self,
            content: str,
            subject: str,
            exam_type: str) -> List[Dict]:
        """Анализирует изменения в открытом банке"""

        updates = []

        subject_keywords = {
            'Математика': ['математика', 'матем', 'math'],
            'Русский язык': ['русский', 'язык', 'russian']
        }

        keywords = subject_keywords.get(subject, [])

        for keyword in keywords:
            if keyword.lower() in content.lower():
                # Ищем новые задания
                import re
                task_links = re.findall(r'href="([^"]*zadaniya[^"]*)"', content)

                for link in task_links:
                    if keyword.lower() in link.lower():
                        updates.append({
                            'type': 'open_bank_task',
                            'subject': subject,
                            'exam_type': exam_type,
                            'url': "{self.base_url}{link}",
                            'title': "Новое задание {subject} ({exam_type})",
                            'timestamp': timezone.now().isoformat()
                        })

        return updates

    def _get_last_content_hash(self, content_type: str) -> Optional[str]:
        """Получает последний хеш контента"""

        try:
            fipi_data = FIPIData.objects.filter(
                data_type='content_hash',
                subject=content_type
            ).order_by('-created_at').first()

            return fipi_data.content_hash if fipi_data else None

        except Exception as e:
            logger.error("Ошибка при получении хеша: {e}")
            return None

    def _save_content_hash(self, content_type: str, content_hash: str):
        """Сохраняет хеш контента"""

        try:
            FIPIData.objects.create(
                title="Content hash for {content_type}",
                url="{self.base_url}/{content_type}",
                data_type='content_hash',
                subject=content_type,
                content_hash=content_hash,
                content=content_hash,
                collected_at=timezone.now(),
                is_processed=True
            )

        except Exception as e:
            logger.error("Ошибка при сохранении хеша: {e}")

    def _save_updates_to_db(self, updates: Dict[str, Any]):
        """Сохраняет обновления в базу данных"""

        try:
            for subject_updates in [
                    updates['math_updates'],
                    updates['russian_updates']]:
                for update in subject_updates:
                    FIPIData.objects.create(
                        title=update['title'],
                        url=update['url'],
                        data_type=update['type'],
                        subject=update['subject'],
                        content_hash=hashlib.md5(update['url'].encode()).hexdigest(),
                        content=update.get('description', ''),
                        collected_at=timezone.now(),
                        is_processed=False
                    )

        except Exception as e:
            logger.error("Ошибка при сохранении обновлений: {e}")

    def _notify_admin(self, updates: Dict[str, Any]):
        """Уведомляет администратора об обновлениях"""

        try:
            # Подготавливаем сообщение
            message = self._prepare_notification_message(updates)

            # Отправляем email
            self._send_email_notification(message)

            # Отправляем в Telegram (если настроен)
            self._send_telegram_notification(message)

            logger.info("Администратор уведомлен об обновлениях")

        except Exception as e:
            logger.error("Ошибка при уведомлении администратора: {e}")

    def _prepare_notification_message(self, updates: Dict[str, Any]) -> str:
        """Подготавливает сообщение для уведомления"""

        message = """
🔄 ОБНОВЛЕНИЯ ФИПИ

Время: {updates['timestamp']}
Всего обновлений: {updates['total_updates']}

📐 МАТЕМАТИКА:
"""

        for update in updates['math_updates']:
            message += "• {update['title']}\n"
            message += "  URL: {update['url']}\n"

        message += "\n📝 РУССКИЙ ЯЗЫК:\n"

        for update in updates['russian_updates']:
            message += "• {update['title']}\n"
            message += "  URL: {update['url']}\n"

        message += "\nПроверьте обновления на сайте ФИПИ."

        return message

    def _send_email_notification(self, message: str):
        """Отправляет email уведомление"""

        try:
            send_mail(
                subject='Обновления ФИПИ - ExamFlow',
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False
            )

        except Exception as e:
            logger.error("Ошибка при отправке email: {e}")

    def _send_telegram_notification(self, message: str):
        """Отправляет уведомление в Telegram"""

        try:
            # Здесь можно добавить отправку в Telegram
            # если есть настроенный бот
            pass

        except Exception as e:
            logger.error("Ошибка при отправке в Telegram: {e}")

    def get_update_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику обновлений"""

        try:
            stats = {
                'total_updates': FIPIData.objects.filter(
                    data_type__in=['demo_variant', 'open_bank_task']
                ).count(),
                'math_updates': FIPIData.objects.filter(
                    subject__icontains='математика'
                ).count(),
                'russian_updates': FIPIData.objects.filter(
                    subject__icontains='русский'
                ).count(),
                'last_check': FIPIData.objects.order_by('-created_at').first().created_at if FIPIData.objects.exists() else None
            }

            return stats

        except Exception as e:
            logger.error("Ошибка при получении статистики: {e}")
            return {}

# Глобальный экземпляр монитора
fipi_monitor = FIPIMonitor()
