"""
Система загрузки и парсинга материалов с сайта ФИПИ
"""

import requests
from bs4 import BeautifulSoup
import time
from urllib.parse import urljoin
from django.db import transaction
from learning.models import ExamType, Subject, Topic, Task
import logging

logger = logging.getLogger(__name__)


class FipiLoader:
    """Загрузчик материалов ФИПИ"""

    def __init__(self):
        self.base_url = "https://fipi.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

        # Структура предметов ФИПИ
        self.subjects_data = {
            'ЕГЭ': {
                'математика': {
                    'name': 'Математика',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/matematika',
                    'icon': 'fas fa-calculator',
                    'color': '#00ff88'
                },
                'русский_язык': {
                    'name': 'Русский язык',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/russkiy-yazyk',
                    'icon': 'fas fa-language',
                    'color': '#00d4ff'
                },
                'физика': {
                    'name': 'Физика',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/fizika',
                    'icon': 'fas fa-atom',
                    'color': '#ff00ff'
                },
                'химия': {
                    'name': 'Химия',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/khimiya',
                    'icon': 'fas fa-flask',
                    'color': '#ffff00'
                },
                'биология': {
                    'name': 'Биология',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/biologiya',
                    'icon': 'fas fa-dna',
                    'color': '#00ff88'
                },
                'история': {
                    'name': 'История',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/istoriya',
                    'icon': 'fas fa-landmark',
                    'color': '#ff0040'
                },
                'обществознание': {
                    'name': 'Обществознание',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/obshchestvoznanie',
                    'icon': 'fas fa-users',
                    'color': '#00d4ff'
                },
                'информатика': {
                    'name': 'Информатика',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/informatika-i-ikt',
                    'icon': 'fas fa-code',
                    'color': '#ff00ff'
                },
                'литература': {
                    'name': 'Литература',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/literatura',
                    'icon': 'fas fa-book-open',
                    'color': '#ffff00'
                },
                'география': {
                    'name': 'География',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/geografiya',
                    'icon': 'fas fa-globe',
                    'color': '#00ff88'
                },
                'английский_язык': {
                    'name': 'Английский язык',
                    'url_path': '/ege/demoversii-specifikacii-kodifikatory/angliyskiy-yazyk',
                    'icon': 'fas fa-language',
                    'color': '#00d4ff'
                }
            },
            'ОГЭ': {
                'математика': {
                    'name': 'Математика',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/matematika',
                    'icon': 'fas fa-calculator',
                    'color': '#00ff88'
                },
                'русский_язык': {
                    'name': 'Русский язык',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/russkiy-yazyk',
                    'icon': 'fas fa-language',
                    'color': '#00d4ff'
                },
                'физика': {
                    'name': 'Физика',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/fizika',
                    'icon': 'fas fa-atom',
                    'color': '#ff00ff'
                },
                'химия': {
                    'name': 'Химия',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/khimiya',
                    'icon': 'fas fa-flask',
                    'color': '#ffff00'
                },
                'биология': {
                    'name': 'Биология',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/biologiya',
                    'icon': 'fas fa-dna',
                    'color': '#00ff88'
                },
                'история': {
                    'name': 'История',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/istoriya',
                    'icon': 'fas fa-landmark',
                    'color': '#ff0040'
                },
                'обществознание': {
                    'name': 'Обществознание',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/obshchestvoznanie',
                    'icon': 'fas fa-users',
                    'color': '#00d4ff'
                },
                'информатика': {
                    'name': 'Информатика',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/informatika-i-ikt',
                    'icon': 'fas fa-code',
                    'color': '#ff00ff'
                },
                'литература': {
                    'name': 'Литература',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/literatura',
                    'icon': 'fas fa-book-open',
                    'color': '#ffff00'
                },
                'география': {
                    'name': 'География',
                    'url_path': '/oge/demoversii-specifikacii-kodifikatory/geografiya',
                    'icon': 'fas fa-globe',
                    'color': '#00ff88'
                }
            }
        }

    def load_subjects(self):
        """Загружает все предметы и их структуру"""
        logger.info("Начинаем загрузку предметов ФИПИ...")

        with transaction.atomic():
            # Создаем типы экзаменов
            ege, _ = ExamType.objects.get_or_create(  # type: ignore
                code='EGE',
                defaults={'name': 'Единый государственный экзамен'}
            )
            oge, _ = ExamType.objects.get_or_create(  # type: ignore
                code='OGE',
                defaults={'name': 'Основной государственный экзамен'}
            )

            exam_types = {'ЕГЭ': ege, 'ОГЭ': oge}

            total_subjects = 0
            total_tasks = 0

            for exam_type_name, subjects in self.subjects_data.items():
                exam_types[exam_type_name]

                for subject_key, subject_data in subjects.items():
                    try:
                        # Создаем предмет
                        subject, created = Subject.objects.get_or_create(  # type: ignore
                            name=subject_data['name'],
                            exam_type=exam_type_name,
                            defaults={
                                'icon': subject_data.get('icon', 'fas fa-book'),
                                'color': subject_data.get('color', '#00ff88')
                            }
                        )

                        if created:
                            total_subjects += 1
                            logger.info(
                                f"Создан предмет: {subject.name} ({exam_type_name})")

                        # Загружаем материалы для предмета
                        tasks_count = self._load_subject_materials(
                            subject, subject_data)
                        total_tasks += tasks_count

                        # Пауза между запросами
                        time.sleep(1)

                    except Exception as e:
                        logger.error(
                            f"Ошибка при загрузке предмета {subject_data['name']}: {str(e)}")
                        continue

            logger.info(
                f"Загрузка завершена. Предметов: {total_subjects}, заданий: {total_tasks}")
            return total_subjects, total_tasks

    def _load_subject_materials(self, subject, subject_data):
        """Загружает материалы для конкретного предмета"""
        try:
            url = urljoin(self.base_url, subject_data['url_path'])
            response = self.session.get(url, timeout=30)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            # Ищем ссылки на демоверсии и материалы
            demo_links = self._find_demo_links(soup)

            tasks_created = 0

            for link_data in demo_links:
                try:
                    # Создаем тему если её нет
                    topic, _ = Topic.objects.get_or_create(  # type: ignore
                        subject=subject,
                        name=link_data.get('topic', 'Демоверсия'),
                        defaults={
                            'code': f"{subject.name.upper()}_DEMO",
                            'description': link_data.get('description', ''),
                            'order': 0
                        }
                    )

                    # Создаем задание
                    task, created = Task.objects.get_or_create(  # type: ignore
                        subject=subject,
                        title=link_data['title'],
                        defaults={
                            'topic': topic,
                            'description': link_data.get('description', ''),
                            'difficulty': self._determine_difficulty(link_data['title']),
                            'answer': 'Ответ будет добавлен после анализа материала',
                            'solution': '',
                            'source': 'ФИПИ',
                            'year': 2025,
                            'tags': link_data.get('tags', ''),
                            'is_active': True
                        }
                    )

                    if created:
                        tasks_created += 1
                        logger.info(f"Создано задание: {task.title}")

                except Exception as e:
                    logger.error(f"Ошибка при создании задания: {str(e)}")
                    continue

            return tasks_created

        except Exception as e:
            logger.error(f"Ошибка при загрузке материалов для {subject.name}: {str(e)}")
            return 0

    def _find_demo_links(self, soup):
        """Находит ссылки на демоверсии и материалы"""
        links = []

        # Ищем различные типы ссылок на материалы
        selectors = [
            'a[href*="demo"]',
            'a[href*="демо"]',
            'a[href*="specification"]',
            'a[href*="спецификация"]',
            'a[href*="kodifikator"]',
            'a[href*="кодификатор"]',
            '.file-link a',
            '.download-link a'
        ]

        for selector in selectors:
            found_links = soup.select(selector)
            for link in found_links:
                href = link.get('href')
                text = link.get_text(strip=True)

                if href and text and len(text) > 5:
                    # Фильтруем только PDF и DOC файлы
                    if any(ext in href.lower() for ext in ['.pdf', '.doc', '.docx']):
                        links.append({
                            'title': text[:200],  # Ограничиваем длину
                            'url': urljoin(self.base_url, href),
                            'description': f"Официальный материал ФИПИ: {text}",
                            'topic': self._extract_topic_from_title(text),
                            'tags': self._extract_tags_from_title(text)
                        })

        # Убираем дубликаты
        unique_links = []
        seen_titles = set()
        for link in links:
            if link['title'] not in seen_titles:
                unique_links.append(link)
                seen_titles.add(link['title'])

        return unique_links[:20]  # Ограничиваем количество

    def _extract_topic_from_title(self, title):
        """Извлекает тему из названия материала"""
        title_lower = title.lower()

        if 'демо' in title_lower or 'demo' in title_lower:
            return 'Демоверсия'
        elif 'спецификация' in title_lower or 'specification' in title_lower:
            return 'Спецификация'
        elif 'кодификатор' in title_lower or 'kodifikator' in title_lower:
            return 'Кодификатор'
        elif 'критерии' in title_lower:
            return 'Критерии оценивания'
        else:
            return 'Дополнительные материалы'

    def _extract_tags_from_title(self, title):
        """Извлекает теги из названия"""
        tags = []
        title_lower = title.lower()

        if '2025' in title:
            tags.append('2025')
        if '2024' in title:
            tags.append('2024')
        if 'базовый' in title_lower:
            tags.append('базовый')
        if 'профильный' in title_lower:
            tags.append('профильный')
        if 'устный' in title_lower:
            tags.append('устный')
        if 'письменный' in title_lower:
            tags.append('письменный')

        return ', '.join(tags)

    def _determine_difficulty(self, title):
        """Определяет сложность по названию"""
        title_lower = title.lower()

        if 'базовый' in title_lower or 'demo' in title_lower:
            return 1
        elif 'профильный' in title_lower or 'критерии' in title_lower:
            return 3
        else:
            return 2

    def create_sample_tasks(self):
        """Создает примеры заданий для всех предметов"""
        logger.info("Создание примеров заданий...")

        sample_tasks = {'Математика': [{'title': 'Найдите значение выражения',
                                        'description': 'Вычислите: 2√3 + 3√3 - √3',
                                        'answer': '4√3',
                                        'solution': '2√3 + 3√3 - √3 = (2 + 3 - 1)√3 = 4√3',
                                        'difficulty': 1},
                                       {'title': 'Решите уравнение',
                                        'description': 'x² - 5x + 6 = 0',
                                        'answer': 'x = 2; x = 3',
                                        'solution': 'По теореме Виета: x₁ + x₂ = 5, x₁ · x₂ = 6. Отсюда x₁ = 2, x₂ = 3',
                                        'difficulty': 2},
                                       {'title': 'Исследование функции',
                                        'description': 'Найдите наибольшее значение функции f(x) = x³ - 3x² + 2 на отрезке [0; 3]',
                                        'answer': '2',
                                        'solution': "f'(x) = 3x² - 6x = 3x(x - 2). Критические точки: x = 0, x = 2. f(0) = 2, f(2) = -2, f(3) = 2. Максимум: 2",
                                        'difficulty': 3}],
                        'Русский язык': [{'title': 'Орфография',
                                          'description': 'В каком слове пишется НН? 1) стари_ый 2) серебря_ый 3) деревя_ый 4) стекля_ый',
                                          'answer': '1',
                                          'solution': 'В слове "старинный" пишется НН, так как оно образовано от существительного "старина" с помощью суффикса -н-',
                                          'difficulty': 1},
                                         {'title': 'Синтаксис',
                                          'description': 'Укажите предложение с обособленным определением',
                                          'answer': 'Вариант с причастным оборотом',
                                          'solution': 'Обособленное определение выделяется запятыми и обычно выражено причастным оборотом',
                                          'difficulty': 2}],
                        'Физика': [{'title': 'Механика',
                                    'description': 'Тело массой 2 кг движется со скоростью 10 м/с. Найдите кинетическую энергию.',
                                    'answer': '100 Дж',
                                    'solution': 'Ek = mv²/2 = 2 · 10²/2 = 100 Дж',
                                    'difficulty': 1},
                                   {'title': 'Электричество',
                                    'description': 'Найдите сопротивление проводника длиной 100 м, сечением 2 мм², удельное сопротивление 0,017 Ом·мм²/м',
                                    'answer': '0,85 Ом',
                                    'solution': 'R = ρl/S = 0,017 · 100/2 = 0,85 Ом',
                                    'difficulty': 2}]}

        tasks_created = 0

        for subject_name, tasks in sample_tasks.items():
            try:
                subjects = Subject.objects.filter(
                    name=subject_name)  # type: ignore  # type: ignore

                for subject in subjects:
                    # Создаем общую тему
                    topic, _ = Topic.objects.get_or_create(  # type: ignore
                        subject=subject,
                        name='Примеры заданий',
                        defaults={
                            'code': f"{subject.name.upper()}_EXAMPLES",
                            'description': 'Примеры заданий для подготовки',
                            'order': 1
                        }
                    )

                    for task_data in tasks:
                        task, created = Task.objects.get_or_create(  # type: ignore
                            subject=subject,
                            title=task_data['title'],
                            defaults={
                                'topic': topic,
                                'description': task_data['description'],
                                'difficulty': task_data['difficulty'],
                                'answer': task_data['answer'],
                                'solution': task_data['solution'],
                                'source': 'ExamFlow Examples',
                                'year': 2025,
                                'is_active': True
                            }
                        )

                        if created:
                            tasks_created += 1

            except Exception as e:
                logger.error(
                    f"Ошибка при создании примеров для {subject_name}: {str(e)}")

        logger.info(f"Создано примеров заданий: {tasks_created}")
        return tasks_created
