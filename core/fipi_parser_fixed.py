"""
Улучшенный парсер для ФИПИ и РешуЕГЭ
Автоматический сбор заданий и обновление базы данных
"""

import requests
import cloudscraper
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import List, Dict, Optional
from django.utils import timezone
from learning.models import Subject, Task
from django.db import transaction

logger = logging.getLogger(__name__)


class FipiParser:
    """Парсер для сайта ФИПИ (fipi.ru)"""

    def __init__(self):
        self.base_url = "https://fipi.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_subjects(self) -> List[Dict]:
        """Получает список предметов с ФИПИ"""
        try:
            response = self.session.get(f"{self.base_url}/ege")
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            subjects = []

            # Ищем ссылки на предметы
            subject_links = soup.find_all('a', href=True)

            for link in subject_links:
                href = link.get('href', '')
                if '/ege/' in href and link.text.strip():
                    subject_name = link.text.strip()
                    if subject_name and len(subject_name) > 2:
                        subjects.append({
                            'name': subject_name,
                            'url': f"{self.base_url}{href}",
                            'source': 'ФИПИ'
                        })

            logger.info(f"Найдено {len(subjects)} предметов на ФИПИ")
            return subjects[:10]  # Ограничиваем для тестирования

        except Exception as e:
            logger.error(f"Ошибка при получении предметов с ФИПИ: {e}")
            return []

    def get_tasks_for_subject(
            self,
            subject_url: str,
            max_tasks: int = 20) -> List[Dict]:
        """Получает задания для конкретного предмета"""
        try:
            response = self.session.get(subject_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            tasks = []

            # Ищем задания (это примерная логика, может потребоваться доработка)
            task_elements = soup.find_all(
                ['div', 'p'], class_=lambda x: x and 'task' in str(x).lower())  # type: ignore

            for i, element in enumerate(task_elements[:max_tasks]):
                if i >= max_tasks:
                    break

                task_text = element.get_text(strip=True)
                if len(task_text) > 20:  # Минимальная длина задания
                    tasks.append({
                        'title': f"Задание {i+1}",
                        'description': task_text[:500],  # Ограничиваем длину
                        'difficulty': random.randint(1, 5),
                        'source': 'ФИПИ',
                        'created_at': timezone.now()
                    })

            logger.info(f"Найдено {len(tasks)} заданий для предмета")
            return tasks

        except Exception as e:
            logger.error(f"Ошибка при получении заданий: {e}")
            return []


class ReshuEGEParser:
    """Парсер для сайта РешуЕГЭ (ege.sdamgia.ru)"""

    def __init__(self):
        self.base_url = "https://ege.sdamgia.ru"
        # Используем cloudscraper для обхода Cloudflare
        self.session = cloudscraper.create_scraper(
            browser={
                "browser": "chrome",
                "platform": "windows",
                "mobile": False,
            }
        )
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        })

    def _get_with_retry(
            self,
            url: str,
            max_retries: int = 3,
            backoff_seconds: float = 2.0):
        """GET с простыми ретраями и паузами при 403/5xx"""
        last_exc: Optional[Exception] = None
        for attempt in range(1, max_retries + 1):
            try:
                resp = self.session.get(url, timeout=20)
                if resp.status_code in (403, 429):
                    # Небольшая пауза и повторная попытка
                    time.sleep(backoff_seconds * attempt)
                    continue
                resp.raise_for_status()
                return resp
            except Exception as exc:  # noqa: BLE001
                last_exc = exc
                time.sleep(backoff_seconds * attempt)
        if last_exc:
            raise last_exc
        raise RuntimeError("Не удалось выполнить запрос без исключения")

    def get_subjects(self) -> List[Dict]:
        """Получает список предметов с РешуЕГЭ"""
        try:
            response = self._get_with_retry(self.base_url)

            soup = BeautifulSoup(response.content, 'html.parser')
            subjects = []

            # Ищем ссылки на предметы
            subject_links = soup.find_all('a', href=True)

            for link in subject_links:
                href = link.get('href', '')
                if '/subject' in href and link.text.strip():
                    subject_name = link.text.strip()
                    if subject_name and len(subject_name) > 2:
                        subjects.append({
                            'name': subject_name,
                            'url': f"{self.base_url}{href}",
                            'source': 'РешуЕГЭ'
                        })

            logger.info(f"Найдено {len(subjects)} предметов на РешуЕГЭ")
            return subjects[:10]  # Ограничиваем для тестирования

        except Exception as e:
            logger.error(f"Ошибка при получении предметов с РешуЕГЭ: {e}")
            return []

    def get_tasks_for_subject(
            self,
            subject_url: str,
            max_tasks: int = 20) -> List[Dict]:
        """Получает задания для конкретного предмета"""
        try:
            response = self._get_with_retry(subject_url)

            soup = BeautifulSoup(response.content, 'html.parser')
            tasks = []

            # Ищем задания
            task_elements = soup.find_all(
                ['div', 'p'], class_=lambda x: x and 'task' in str(x).lower())  # type: ignore

            for i, element in enumerate(task_elements[:max_tasks]):
                if i >= max_tasks:
                    break

                task_text = element.get_text(strip=True)
                if len(task_text) > 20:
                    tasks.append({
                        'title': f"Задание {i+1}",
                        'description': task_text[:500],
                        'difficulty': random.randint(1, 5),
                        'source': 'РешуЕГЭ',
                        'created_at': timezone.now()
                    })

            logger.info(f"Найдено {len(tasks)} заданий для предмета")
            return tasks

        except Exception as e:
            logger.error(f"Ошибка при получении заданий: {e}")
            return []


class DataIntegrator:
    """Интегратор данных в базу данных"""

    def __init__(self):
        self.fipi_parser = FipiParser()
        self.reshu_parser = ReshuEGEParser()

    def integrate_subjects_and_tasks(self, max_tasks_per_subject: int = 20) -> Dict:
        """Интегрирует предметы и задания в базу данных"""
        results = {
            'subjects_created': 0,
            'tasks_created': 0,
            'errors': []
        }

        try:
            # Получаем данные с ФИПИ
            logger.info("🔍 Получение данных с ФИПИ...")
            fipi_subjects = self.fipi_parser.get_subjects()

            for subject_data in fipi_subjects:
                try:
                    with transaction.atomic():
                        # Создаем или получаем предмет
                        subject, created = Subject.objects.get_or_create(  # type: ignore
                            name=subject_data['name'],
                            defaults={
                                'exam_type': 'ЕГЭ'
                            }
                        )

                        if created:
                            results['subjects_created'] += 1
                            logger.info(f"✅ Создан предмет: {subject_data['name']}")

                        # Получаем задания для предмета
                        tasks = self.fipi_parser.get_tasks_for_subject(
                            subject_data['url'],
                            max_tasks_per_subject
                        )

                        # Создаем задания
                        for task_data in tasks:
                            task, created = Task.objects.get_or_create(  # type: ignore
                                title=task_data['title'],
                                subject=subject,
                                defaults={
                                    'description': task_data['description'],
                                    'difficulty': task_data['difficulty'],
                                    'source': task_data['source'],
                                    'created_at': task_data['created_at']
                                }
                            )

                            if created:
                                results['tasks_created'] += 1

                        logger.info(
                            f"📚 Обработано {len(tasks)} заданий для {subject_data['name']}")

                        # Небольшая задержка между запросами
                        time.sleep(random.uniform(1, 3))

                except Exception as e:
                    error_msg = f"Ошибка при обработке предмета {subject_data['name']}: {e}"
                    results['errors'].append(error_msg)
                    logger.error(error_msg)

            # Парсинг РешуЕГЭ временно отключен по запросу пользователя
            logger.info("⏸️ Парсинг РешуЕГЭ отключён. Обрабатываем только ФИПИ.")

            logger.info("🎉 Интеграция данных завершена!")
            return results

        except Exception as e:
            error_msg = f"Критическая ошибка при интеграции: {e}"
            results['errors'].append(error_msg)
            logger.error(error_msg)
            return results


def run_full_parsing(max_tasks_per_subject: int = 20) -> bool:
    """Запускает полный парсинг"""
    try:
        integrator = DataIntegrator()
        results = integrator.integrate_subjects_and_tasks(max_tasks_per_subject)

        logger.info(f"📊 Результаты парсинга:")
        logger.info(f"   Предметов создано: {results['subjects_created']}")
        logger.info(f"   Заданий создано: {results['tasks_created']}")

        if results['errors']:
            logger.warning(f"⚠️  Ошибок: {len(results['errors'])}")
            for error in results['errors'][:5]:  # Показываем первые 5 ошибок
                logger.warning(f"   {error}")

        return len(results['errors']) == 0 or results['tasks_created'] > 0

    except Exception as e:
        logger.error(f"❌ Ошибка при запуске парсинга: {e}")
        return False
