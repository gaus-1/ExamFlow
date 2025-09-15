"""
Улучшенный парсер для ФИПИ и РешуЕГЭ

Автоматически собирает задания и обновляет базу данных
Использует бесплатные методы: requests + BeautifulSoup
"""

import requests
from bs4 import BeautifulSoup
import logging
import time
import random
from typing import List, Dict
from django.db import transaction
from learning.models import Subject, Task
from django.utils import timezone

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
            response = self.session.get("{self.base_url}/ege")
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            subjects = []

            # Ищем ссылки на предметы
            subject_links = soup.find_all('a', href=True)

            for link in subject_links:
                href = link.get('hre', '')
                if '/ege/' in href and href != '/ege':
                    subject_name = link.get_text(strip=True)
                    if subject_name and len(subject_name) > 2:
                        subjects.append({
                            'name': subject_name,
                            'url': "{self.base_url}{href}",
                            'source': 'ФИПИ'
                        })

            logger.info("Найдено {len(subjects)} предметов на ФИПИ")
            return subjects

        except Exception as e:
            logger.error("Ошибка получения предметов с ФИПИ: {e}")
            return []

    def get_tasks_for_subject(self, subject_url: str, subject_name: str) -> List[Dict]:
        """Получает задания для конкретного предмета"""
        try:
            response = self.session.get(subject_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            tasks = []

            # Ищем задания (обычно в таблицах или списках)
            task_elements = soup.find_all(

            for element in task_elements:
                try:
                    title = element.get_text(strip=True)[:200]  # Ограничиваем длину
                    if len(title) > 10:  # Минимальная длина названия
                        task = {
                            'title': title,
                            'description': title,  # Используем название как описание
                            'difficulty': random.randint(1, 5),  # Случайная сложность
                            'source': 'ФИПИ',
                            'subject_name': subject_name
                        }
                        tasks.append(task)
                except Exception as task_error:
                    logger.warning("Ошибка парсинга задания: {task_error}")
                    continue

            logger.info("Найдено {len(tasks)} заданий для предмета {subject_name}")
            return tasks

        except Exception as e:
            logger.error("Ошибка получения заданий для {subject_name}: {e}")
            return []

class ReshuEGEParser:
    """Парсер для сайта РешуЕГЭ (ege.sdamgia.ru)"""

    def __init__(self):
        self.base_url = "https://ege.sdamgia.ru"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def get_subjects(self) -> List[Dict]:
        """Получает список предметов с РешуЕГЭ"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            subjects = []

            # Ищем ссылки на предметы
            subject_links = soup.find_all('a', href=True)

            for link in subject_links:
                href = link.get('hre', '')
                if '/test' in href:
                    subject_name = link.get_text(strip=True)
                    if subject_name and len(subject_name) > 2:
                        subjects.append({
                            'name': subject_name,
                            'url': "{self.base_url}{href}",
                            'source': 'РешуЕГЭ'
                        })

            logger.info("Найдено {len(subjects)} предметов на РешуЕГЭ")
            return subjects

        except Exception as e:
            logger.error("Ошибка получения предметов с РешуЕГЭ: {e}")
            return []

    def get_tasks_for_subject(self, subject_url: str, subject_name: str) -> List[Dict]:
        """Получает задания для конкретного предмета"""
        try:
            response = self.session.get(subject_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')
            tasks = []

            # Ищем задания
            task_elements = soup.find_all(

            for element in task_elements:
                try:
                    title = element.get_text(strip=True)[:200]
                    if len(title) > 10:
                        task = {
                            'title': title,
                            'description': title,
                            'difficulty': random.randint(1, 5),
                            'source': 'РешуЕГЭ',
                            'subject_name': subject_name
                        }
                        tasks.append(task)
                except Exception as task_error:
                    logger.warning("Ошибка парсинга задания: {task_error}")
                    continue

            logger.info("Найдено {len(tasks)} заданий для предмета {subject_name}")
            return tasks

        except Exception as e:
            logger.error("Ошибка получения заданий для {subject_name}: {e}")
            return []

class DataIntegrator:
    """Интегратор данных в базу Django"""

    def __init__(self):
        self.fipi_parser = FipiParser()
        self.reshu_parser = ReshuEGEParser()

    def create_or_update_subject(self, subject_data: Dict) -> Subject:
        """Создает или обновляет предмет в базе"""
        try:
            # Определяем тип экзамена по названию
            exam_type = 'ЕГЭ' if any(
                word in subject_data['name'].lower() for word in [
                    'егэ', 'егэ', 'профиль', 'база']) else 'ОГЭ'

            subject, created = Subject.objects.get_or_create(  # type: ignore
                name=subject_data['name'],
                defaults={
                    'exam_type': exam_type
                }
            )

            if created:
                logger.info("Создан новый предмет: {subject_data['name']}")
            else:
                logger.info("Предмет уже существует: {subject_data['name']}")

            return subject

        except Exception as e:
            logger.error("Ошибка создания предмета {subject_data['name']}: {e}")
            raise

    def create_or_update_task(self, task_data: Dict, subject: Subject) -> Task:
        """Создает или обновляет задание в базе"""
        try:
            # Проверяем, не существует ли уже такое задание
            existing_task = Task.objects.filter(  # type: ignore
                title=task_data['title'][:200],  # Ограничиваем длину
                subject=subject
            ).first()

            if existing_task:
                logger.debug("Задание уже существует: {task_data['title'][:50]}...")
                return existing_task

            # Создаем новое задание
            task = Task.objects.create(  # type: ignore
                subject=subject,
                title=task_data['title'][:200],
                description=task_data['description'][:1000],
                difficulty=task_data['difficulty'],
                source=task_data['source'],
                created_at=timezone.now()
            )

            logger.info("Создано новое задание: {task_data['title'][:50]}...")
            return task

        except Exception as e:
            logger.error("Ошибка создания задания: {e}")
            raise

    def run_data_update(self, max_tasks_per_subject: int = 50) -> Dict:
        """Запускает полное обновление данных"""
        start_time = time.time()
        total_subjects = 0
        total_tasks = 0
        errors = []

        try:
            logger.info("🚀 Начинаем обновление базы данных...")

            # Получаем данные с ФИПИ
            logger.info("📚 Получаем данные с ФИПИ...")
            fipi_subjects = self.fipi_parser.get_subjects()

            # Получаем данные с РешуЕГЭ
            logger.info("📚 Получаем данные с РешуЕГЭ...")
            reshu_subjects = self.reshu_parser.get_subjects()

            # Объединяем предметы
            all_subjects = fipi_subjects + reshu_subjects

            # Убираем дубликаты по названию
            unique_subjects = {}
            for subject in all_subjects:
                name = subject['name'].strip()
                if name not in unique_subjects:
                    unique_subjects[name] = subject

            logger.info("📊 Найдено {len(unique_subjects)} уникальных предметов")

            # Обрабатываем каждый предмет
            for subject_data in unique_subjects.values():
                try:
                    # Создаем или обновляем предмет
                    subject = self.create_or_update_subject(subject_data)
                    total_subjects += 1

                    # Получаем задания
                    if subject_data['source'] == 'ФИПИ':
                        tasks = self.fipi_parser.get_tasks_for_subject(
                            subject_data['url'], subject_data['name']
                        )
                    else:
                        tasks = self.reshu_parser.get_tasks_for_subject(
                            subject_data['url'], subject_data['name']
                        )

                    # Ограничиваем количество заданий
                    tasks = tasks[:max_tasks_per_subject]

                    # Создаем задания в базе
                    with transaction.atomic():
                        for task_data in tasks:
                            try:
                                self.create_or_update_task(task_data, subject)
                                total_tasks += 1
                            except Exception as task_error:
                                errors.append("Ошибка создания задания: {task_error}")
                                continue

                    # Небольшая пауза между предметами
                    time.sleep(random.uniform(1, 3))

                except Exception as subject_error:
                    error_msg = "Ошибка обработки предмета {subject_data['name']}: {subject_error}"
                    errors.append(error_msg)
                    logger.error(error_msg)
                    continue

            # Выводим статистику
            execution_time = time.time() - start_time
            logger.info("✅ Обновление завершено за {execution_time:.2f} секунд")
            logger.info("📊 Обработано предметов: {total_subjects}")
            logger.info("📝 Создано/обновлено заданий: {total_tasks}")

            if errors:
                logger.warning("⚠️ Найдено {len(errors)} ошибок")
                for error in errors[:5]:  # Показываем первые 5 ошибок
                    logger.warning("  - {error}")

            return {
                'success': True,
                'subjects_processed': total_subjects,
                'tasks_processed': total_tasks,
                'execution_time': execution_time,
                'errors': errors
            }

        except Exception as e:
            logger.error("❌ Критическая ошибка обновления: {e}")
            return {
                'success': False,
                'error': str(e),
                'subjects_processed': total_subjects,
                'tasks_processed': total_tasks,
                'execution_time': time.time() - start_time
            }

def run_data_update():
    """Функция для запуска обновления данных"""
    integrator = DataIntegrator()
    return integrator.run_data_update()

if __name__ == "__main__":
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    # Запуск обновления
    result = run_data_update()

    if result['success']:
        print("✅ Обновление успешно завершено!")
        print("📊 Предметов: {result['subjects_processed']}")
        print("📝 Заданий: {result['tasks_processed']}")
        print("⏱️ Время: {result['execution_time']:.2f} сек")
    else:
        print("❌ Ошибка обновления: {result['error']}")
