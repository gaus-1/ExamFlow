"""
Промышленный скрапер для сбора данных с сайта ФИПИ
Поддерживает все типы контента: HTML, PDF, DOC, XLS
Интегрирован с картой источников FIPISourceMap
"""

import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, List, Optional
from urllib.parse import urljoin
import hashlib
import re
import time
from django.utils import timezone

from core.models import FIPIData, FIPISourceMap

logger = logging.getLogger(__name__)


class AdvancedFIPIScraper:
    """Промышленный скрапер для сбора данных с сайта ФИПИ"""

    def __init__(self):
        self.base_url = "https://fipi.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

        # Паттерны для определения типов контента
        self.content_patterns = {
            'demo_variant': [
                r'демоверс',
                r'демо-вариант',
                r'демонстрационный',
                r'демо версия'
            ],
            'specification': [
                r'спецификац',
                r'специфик'
            ],
            'codefier': [
                r'кодификатор',
                r'кодифик'
            ],
            'open_bank_task': [
                r'открытый банк',
                r'банк заданий',
                r'открытый банк заданий'
            ]
        }

        # Предметы для ЕГЭ и ОГЭ
        self.subjects = {
            'russian': ['русский', 'русск'],
            'mathematics': ['математик', 'матем'],
            'physics': ['физик', 'физ'],
            'chemistry': ['хими', 'хим'],
            'biology': ['биолог', 'биол'],
            'history': ['истори', 'истор'],
            'geography': ['географ', 'геогр'],
            'social_studies': ['обществознан', 'обществ'],
            'literature': ['литератур', 'литер'],
            'foreign_language': ['иностранн', 'английск', 'немецк', 'франц', 'испанск'],
            'informatics': ['информатик', 'информ']
        }

    def get_page_content(self, url: str) -> Optional[str]:
        """Получает содержимое страницы с обработкой ошибок"""
        try:
            logger.info(f"Получаем содержимое: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            # Проверяем тип контента
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type and 'application/pdf' not in content_type:
                logger.warning(f"Неожиданный тип контента: {content_type} для {url}")

            if 'text/html' in content_type:
                return response.text
            else:
                # Для PDF и других бинарных файлов возвращаем строковое представление
                return str(response.content)

        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка при получении страницы {url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении {url}: {e}")
            return None

    def extract_links_from_page(self, url: str) -> List[Dict]:
        """Извлекает все ссылки со страницы"""
        content = self.get_page_content(url)
        if not content:
            return []

        try:
            soup = BeautifulSoup(content, 'html.parser')
            links = []

            # Ищем все ссылки
            for link in soup.find_all('a', href=True):
                href = link['href']
                title = link.get_text(strip=True)

                # Преобразуем относительные ссылки в абсолютные
                if href.startswith('/'):
                    href = urljoin(self.base_url, href)
                elif not href.startswith('http'):
                    href = urljoin(url, href)

                # Фильтруем только ссылки на fipi.ru
                if 'fipi.ru' in href:
                    links.append({
                        'url': href,
                        'title': title,
                        'text': link.get_text(strip=True)
                    })

            return links

        except Exception as e:
            logger.error(f"Ошибка при парсинге ссылок с {url}: {e}")
            return []

    def detect_content_type(self, url: str, title: str, content: str = "") -> str:
        """Определяет тип контента по URL, заголовку и содержимому"""
        text_to_analyze = f"{url} {title} {content}".lower()

        for content_type, patterns in self.content_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_to_analyze):
                    return content_type

        return 'unknown'

    def detect_subject(self, url: str, title: str) -> Optional[str]:
        """Определяет предмет по URL и заголовку"""
        text_to_analyze = f"{url} {title}".lower()

        for subject, keywords in self.subjects.items():
            for keyword in keywords:
                if keyword in text_to_analyze:
                    return subject

        return None

    def detect_exam_type(self, url: str) -> str:
        """Определяет тип экзамена по URL"""
        if '/ege/' in url:
            return 'ege'
        elif '/oge/' in url:
            return 'oge'
        elif '/gve-11/' in url:
            return 'gve_11'
        elif '/gve-9/' in url:
            return 'gve_9'
        elif '/essay/' in url:
            return 'essay'
        elif '/interview/' in url:
            return 'interview'
        else:
            return 'ege'  # По умолчанию ЕГЭ

    def get_content_hash(self, content: str) -> str:
        """Создает хеш содержимого"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    def collect_from_source_map(self) -> Dict:
        """Собирает данные на основе карты источников.
        Для индекс-страниц: парсит все ссылки и классифицирует.
        Для конкретных страниц/файлов: сохраняет как есть.
        """
        logger.info("Собираем данные на основе карты источников...")

        sources = FIPISourceMap.objects.filter(is_active=True)  # type: ignore
        results = {
            'demo_variant': [],
            'specification': [],
            'codefier': [],
            'open_bank_task': [],
            'methodical_material': [],
            'news': [],
            'document': []
        }

        for source in sources:
            try:
                logger.info(f"Обрабатываем источник: {source.name}")

                # Получаем содержимое индекс-страницы
                page_content = self.get_page_content(source.url)
                if not page_content:
                    continue

                # Для индекс-страниц парсим ссылки
                links = self.extract_links_from_page(source.url)
                if links:
                    saved_on_page = 0
                    for link in links:
                        link_url = link['url']
                        link_title = link['title']

                        # Классифицируем тип контента и предмет
                        detected_type = self.detect_content_type(
                            link_url, link_title, page_content)
                        detected_subject = self.detect_subject(link_url, link_title)
                        exam_type = self.detect_exam_type(link_url)

                        # Пропускаем нерелевантные
                        if detected_type == 'unknown':
                            continue

                        # Загружаем содержимое ссылки (ограниченно)
                        link_content = self.get_page_content(link_url) or ''

                        # Для демо/спецификаций/кодификаторов: если ссылка не .pdf,
                        # пытаемся найти внутри страницы реальные PDF-ссылки и сохранить
                        # их
                        if detected_type in [
                            'demo_variant',
                            'specification',
                                'codefier'] and not link_url.lower().endswith('.pdf'):
                            try:
                                soup = BeautifulSoup(link_content, 'html.parser')
                                pdf_links = []
                                for a in soup.find_all('a', href=True):
                                    href = a['href']
                                    if href.lower().endswith('.pdf'):
                                        if href.startswith('/'):
                                            href = urljoin(self.base_url, href)
                                        elif not href.startswith('http'):
                                            href = urljoin(link_url, href)
                                        pdf_links.append(
                                            (href, a.get_text(strip=True) or link_title))

                                # Резервный поиск PDF через regex, если ничего не нашли
                                if not pdf_links:
                                    try:
                                        for href in re.findall(
                                                r"href=['\"]([^'\"]+\.pdf)['\"]", link_content, flags=re.IGNORECASE):
                                            norm = href
                                            if norm.startswith('/'):
                                                norm = urljoin(self.base_url, norm)
                                            elif not norm.startswith('http'):
                                                norm = urljoin(link_url, norm)
                                            pdf_links.append((norm, link_title))
                                    except Exception:
                                        pass

                                for pdf_url, pdf_title in pdf_links:
                                    pdf_hash = self.get_content_hash(pdf_url)
                                    if FIPIData.objects.filter(
                                            content_hash=pdf_hash).exists():  # type: ignore
                                        continue
                                    FIPIData.objects.create(  # type: ignore
                                        title=pdf_title or source.name,
                                        url=pdf_url,
                                        data_type=detected_type,
                                        subject=detected_subject,
                                        exam_type=exam_type,
                                        content_hash=pdf_hash,
                                        content='',
                                        collected_at=timezone.now()
                                    )
                                    saved_on_page += 1
                            except Exception as e:
                                logger.warning(
                                    f"Не удалось извлечь PDF-ссылки с {link_url}: {e}")
                                # продолжаем обычную обработку как HTML

                        else:
                            # Обычная запись: HTML или прямая PDF
                            content_hash = self.get_content_hash(
                                (link_content or '')[:5000] + link_url)
                            if FIPIData.objects.filter(
                                    content_hash=content_hash).exists():  # type: ignore
                                continue
                            FIPIData.objects.create(  # type: ignore
                                title=link_title or source.name,
                                url=link_url,
                                data_type=detected_type,
                                subject=detected_subject,
                                exam_type=exam_type,
                                content_hash=content_hash,
                                content=str(link_content)[:10000],
                                collected_at=timezone.now()
                            )
                            saved_on_page += 1

                    logger.info(
                        f"С индекс-страницы {source.url} сохранено {saved_on_page} элементов")
                    source.mark_as_checked(self.get_content_hash(page_content))
                    # Пауза между индекс-страницами
                    time.sleep(1)
                    continue

                # Если это не индекс-страница, сохраняем саму страницу
                content_hash = self.get_content_hash(page_content)
                if not FIPIData.objects.filter(
                        content_hash=content_hash).exists():  # type: ignore
                    FIPIData.objects.create(  # type: ignore
                        title=source.name,
                        url=source.url,
                        data_type=source.data_type,
                        subject=source.subject,
                        exam_type=source.exam_type,
                        content_hash=content_hash,
                        content=str(page_content)[:10000],
                        collected_at=timezone.now()
                    )

                source.mark_as_checked(content_hash)
                time.sleep(0.5)

            except Exception as e:
                logger.error(f"Ошибка при обработке источника {source.name}: {e}")
                continue

        # Возвращаем агрегированную статистику
        stats = self.get_statistics()
        logger.info(f"Сбор завершен. {stats}")
        return results

    def save_to_database(self, data: Dict) -> bool:
        """Сохраняет данные в базу данных"""
        try:
            total_saved = 0
            total_skipped = 0

            for data_type, items in data.items():
                for item in items:
                    # Создаем хеш содержимого
                    content_hash = item.get('content_hash') or hashlib.sha256(
                        item.get('content', '').encode('utf-8')
                    ).hexdigest()

                    # Проверяем, есть ли уже такая запись
                    if FIPIData.objects.filter(
                            content_hash=content_hash).exists():  # type: ignore
                        total_skipped += 1
                        continue

                    # Создаем новую запись
                    FIPIData.objects.create(  # type: ignore
                        title=item.get('title', ''),
                        url=item.get('url', ''),
                        data_type=data_type,
                        subject=item.get('subject'),
                        content_hash=content_hash,
                        content=item.get('content', ''),
                        collected_at=timezone.now()
                    )
                    total_saved += 1

            logger.info(f"Сохранено {total_saved} записей, пропущено {total_skipped}")
            return True

        except Exception as e:
            logger.error(f"Ошибка при сохранении данных: {e}")
            return False

    def get_statistics(self) -> Dict:
        """Получает статистику по собранным данным"""
        stats = {
            'total_sources': FIPISourceMap.objects.count(),  # type: ignore
            # type: ignore
            'active_sources': FIPISourceMap.objects.filter(is_active=True).count(),
            'total_data': FIPIData.objects.count(),  # type: ignore
            # type: ignore
            'processed_data': FIPIData.objects.filter(is_processed=True).count(),
            'by_type': {},
            'by_priority': {}
        }

        # Статистика по типам данных
        for data_type, _ in FIPIData.DATA_TYPES:
            count = FIPIData.objects.filter(data_type=data_type).count()  # type: ignore
            if count > 0:
                stats['by_type'][data_type] = count

        # Статистика по приоритетам источников
        for priority in [1, 2, 3, 4]:
            count = FIPISourceMap.objects.filter(
                priority=priority).count()  # type: ignore
            if count > 0:
                stats['by_priority'][priority] = count

        return stats
