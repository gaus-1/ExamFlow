"""
Скрапер для сбора данных с сайта ФИПИ (fipi.ru)
"""

import requests
import logging
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import time
import hashlib
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FIPIScraper:
    """
    Класс для сбора данных с сайта ФИПИ
    """

    def __init__(self):
        self.base_url = "https://fipi.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Ключевые разделы ФИПИ для сбора данных
        self.target_sections = {
            'demo_variants': '/ege/demoversii-specifikacii-kodifikatory',
            'open_bank': '/ege/otkrytyy-bank-zadaniy-ege',
            'specifications': '/ege/specifikacii-kodifikatory',
            'codifiers': '/ege/kodifikatory'
        }

        # Предметы ЕГЭ
        self.subjects = {
            'mathematics': 'Математика',
            'russian': 'Русский язык',
            'physics': 'Физика',
            'chemistry': 'Химия',
            'biology': 'Биология',
            'history': 'История',
            'social_studies': 'Обществознание',
            'english': 'Английский язык',
            'informatics': 'Информатика и ИКТ',
            'geography': 'География',
            'literature': 'Литература'
        }

    def get_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """
        Получает содержимое страницы
        """
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            return None

    def extract_demo_variants(self) -> List[Dict]:
        """
        Извлекает демонстрационные варианты
        """
        logger.info("Начинаем сбор демонстрационных вариантов...")
        variants = []

        url = urljoin(self.base_url, self.target_sections['demo_variants'])
        soup = self.get_page_content(url)

        if not soup:
            return variants

        # Ищем ссылки на демонстрационные варианты
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)

            # Фильтруем ссылки на демонстрационные варианты
            if any(keyword in text.lower()
                   for keyword in ['демо', 'демонстрационный', 'вариант']):
                full_url = urljoin(self.base_url, href)

                variant_data = {
                    'title': text,
                    'url': full_url,
                    'type': 'demo_variant',
                    'subject': self._detect_subject(text),
                    'collected_at': datetime.now().isoformat(),
                    'content_hash': hashlib.md5(full_url.encode()).hexdigest()
                }

                variants.append(variant_data)
                logger.info(f"Найден демонстрационный вариант: {text}")

        return variants

    def extract_open_bank_tasks(self) -> List[Dict]:
        """
        Извлекает задания из открытого банка
        """
        logger.info("Начинаем сбор заданий из открытого банка...")
        tasks = []

        url = urljoin(self.base_url, self.target_sections['open_bank'])
        soup = self.get_page_content(url)

        if not soup:
            return tasks

        # Ищем ссылки на предметы
        subject_links = soup.find_all('a', href=True)

        for link in subject_links:
            href = link.get('href')
            text = link.get_text(strip=True)

            # Проверяем, является ли ссылка предметом
            if any(subject in text for subject in self.subjects.values()):
                subject_url = urljoin(self.base_url, href)
                subject_tasks = self._extract_subject_tasks(subject_url, text)
                tasks.extend(subject_tasks)

        return tasks

    def _extract_subject_tasks(self, subject_url: str, subject_name: str) -> List[Dict]:
        """
        Извлекает задания для конкретного предмета
        """
        tasks = []
        soup = self.get_page_content(subject_url)

        if not soup:
            return tasks

        # Ищем темы и задания
        topic_links = soup.find_all('a', href=True)

        for link in topic_links:
            href = link.get('href')
            text = link.get_text(strip=True)

            if 'задание' in text.lower() or 'тема' in text.lower():
                task_url = urljoin(self.base_url, href)
                task_data = {
                    'title': text,
                    'url': task_url,
                    'type': 'open_bank_task',
                    'subject': subject_name,
                    'collected_at': datetime.now().isoformat(),
                    'content_hash': hashlib.md5(task_url.encode()).hexdigest()
                }
                tasks.append(task_data)

        return tasks

    def extract_specifications(self) -> List[Dict]:
        """
        Извлекает спецификации
        """
        logger.info("Начинаем сбор спецификаций...")
        specs = []

        url = urljoin(self.base_url, self.target_sections['specifications'])
        soup = self.get_page_content(url)

        if not soup:
            return specs

        # Ищем ссылки на спецификации
        links = soup.find_all('a', href=True)

        for link in links:
            href = link.get('href')
            text = link.get_text(strip=True)

            if 'спецификация' in text.lower():
                full_url = urljoin(self.base_url, href)

                spec_data = {
                    'title': text,
                    'url': full_url,
                    'type': 'specification',
                    'subject': self._detect_subject(text),
                    'collected_at': datetime.now().isoformat(),
                    'content_hash': hashlib.md5(full_url.encode()).hexdigest()
                }

                specs.append(spec_data)
                logger.info(f"Найдена спецификация: {text}")

        return specs

    def _detect_subject(self, text: str) -> Optional[str]:
        """
        Определяет предмет по тексту
        """
        text_lower = text.lower()

        for subject_key, subject_name in self.subjects.items():
            if subject_name.lower() in text_lower:
                return subject_name

        return None

    def collect_all_data(self) -> Dict[str, List[Dict]]:
        """
        Собирает все данные с ФИПИ
        """
        logger.info("Начинаем полный сбор данных с ФИПИ...")

        all_data = {
            'demo_variants': [],
            'open_bank_tasks': [],
            'specifications': []
        }

        try:
            # Собираем демонстрационные варианты
            all_data['demo_variants'] = self.extract_demo_variants()
            time.sleep(2)  # Пауза между запросами

            # Собираем задания из открытого банка
            all_data['open_bank_tasks'] = self.extract_open_bank_tasks()
            time.sleep(2)

            # Собираем спецификации
            all_data['specifications'] = self.extract_specifications()

            logger.info(f"Сбор данных завершен. Найдено:")
            logger.info(
                f"- Демонстрационных вариантов: {len(all_data['demo_variants'])}")
            logger.info(
                f"- Заданий из открытого банка: {len(all_data['open_bank_tasks'])}")
            logger.info(f"- Спецификаций: {len(all_data['specifications'])}")

        except Exception as e:
            logger.error(f"Ошибка при сборе данных: {e}")

        return all_data

    def save_to_database(self, data: Dict[str, List[Dict]]) -> bool:
        """
        Сохраняет собранные данные в базу данных
        """
        try:
            from core.models import FIPIData

            saved_count = 0

            for data_type, items in data.items():
                for item in items:
                    # Проверяем, существует ли уже такая запись
                    existing = FIPIData.objects.filter(  # type: ignore
                        content_hash=item['content_hash']
                    ).first()

                    if not existing:
                        FIPIData.objects.create(  # type: ignore
                            title=item['title'],
                            url=item['url'],
                            data_type=data_type,
                            subject=item.get('subject'),
                            content_hash=item['content_hash'],
                            collected_at=datetime.fromisoformat(item['collected_at'])
                        )
                        saved_count += 1

            logger.info(f"Сохранено {saved_count} новых записей в базу данных")
            return True

        except Exception as e:
            logger.error(f"Ошибка при сохранении в базу данных: {e}")
            return False
