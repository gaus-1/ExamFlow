"""
Тесты для фокусировки ExamFlow на математике и русском языке
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from learning.models import Subject, Topic, Task
from core.ai.priority_manager import AIPriorityManager
from core.fipi_monitor import FIPIMonitor
import json

class MathRussianFocusTestCase(TestCase):
    """Тесты фокусировки на математике и русском языке"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()

        # Создаем пользователя
        self.user = User.objects.create_user( # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # Создаем основные предметы
        self.math_prof = Subject.objects.create( # type: ignore
            name='Математика (профильная)',
            code='math_pro',
            exam_type='ЕГЭ',
            description='Профильная математика ЕГЭ - задания 1-19',
            icon='📐',
            is_primary=True
        )

        self.math_base = Subject.objects.create( # type: ignore
            name='Математика (непрофильная)',
            code='math_base',
            exam_type='ЕГЭ',
            description='Базовая математика ЕГЭ - задания 1-20',
            icon='📊',
            is_primary=True
        )

        self.math_oge = Subject.objects.create( # type: ignore
            name='Математика (ОГЭ)',
            code='math_oge',
            exam_type='ОГЭ',
            description='Математика ОГЭ - задания 1-26',
            icon='🔢',
            is_primary=True
        )

        self.russian_ege = Subject.objects.create( # type: ignore
            name='Русский язык (ЕГЭ)',
            code='russian_ege',
            exam_type='ЕГЭ',
            description='Русский язык ЕГЭ - сочинение, тесты, грамматика',
            icon='📝',
            is_primary=True
        )

        self.russian_oge = Subject.objects.create( # type: ignore
            name='Русский язык (ОГЭ)',
            code='russian_oge',
            exam_type='ОГЭ',
            description='Русский язык ОГЭ - изложение, сочинение, тесты',
            icon='📖',
            is_primary=True
        )

        # Создаем архивированные предметы
        self.physics = Subject.objects.create( # type: ignore
            name='Физика',
            code='physics',
            exam_type='ЕГЭ',
            is_archived=True
        )

        self.chemistry = Subject.objects.create( # type: ignore
            name='Химия',
            code='chemistry',
            exam_type='ЕГЭ',
            is_archived=True
        )

        # Создаем темы
        self.math_topic = Topic.objects.create( # type: ignore
            name='Алгебра',
            subject=self.math_prof,
            description='Алгебраические выражения и уравнения'
        )

        self.russian_topic = Topic.objects.create( # type: ignore
            name='Сочинение',
            subject=self.russian_ege,
            description='Написание сочинения по русскому языку'
        )

        # Создаем задания
        self.math_task = Task.objects.create( # type: ignore
            title='Квадратное уравнение',
            description='Решите квадратное уравнение x² - 5x + 6 = 0',
            subject=self.math_prof,
            topic=self.math_topic,
            difficulty='medium'
        )

        self.russian_task = Task.objects.create( # type: ignore     
            title='Сочинение по тексту',
            description='Напишите сочинение по предложенному тексту',
            subject=self.russian_ege,
            topic=self.russian_topic,
            difficulty='hard'
        )

    def test_subjects_list_shows_only_primary(self):
        """Тест: список предметов показывает только основные"""
        response = self.client.get(reverse('learning:subjects_list'))

        self.assertEqual(response.status_code, 200) # type: ignore

        # Проверяем, что показываются основные предметы
        self.assertContains(response, 'Математика (профильная)')
        self.assertContains(response, 'Математика (непрофильная)')
        self.assertContains(response, 'Математика (ОГЭ)')
        self.assertContains(response, 'Русский язык (ЕГЭ)')
        self.assertContains(response, 'Русский язык (ОГЭ)')

        # Проверяем, что НЕ показываются архивированные предметы
        self.assertNotContains(response, 'Физика')
        self.assertNotContains(response, 'Химия')

    def test_math_subject_detail(self):
        """Тест: детальная страница математики"""
        response = self.client.get(reverse('learning:math_subject_detail', args=[self.math_prof.id]))

        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertContains(response, 'Математика (профильная)')
        self.assertContains(response, 'Алгебра')

    def test_russian_subject_detail(self):
        """Тест: детальная страница русского языка"""
        response = self.client.get(reverse('learning:russian_subject_detail', args=[self.russian_ege.id]))

        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertContains(response, 'Русский язык (ЕГЭ)')
        self.assertContains(response, 'Сочинение')

    def test_focused_search_math(self):
        """Тест: фокусированный поиск по математике"""
        response = self.client.get(reverse('learning:focused_search'), {'q': 'уравнение'})

        self.assertEqual(response.status_code, 200) # type: ignore

        data = json.loads(response.content) # type: ignore
        self.assertGreater(len(data['results']), 0) # type: ignore

        # Проверяем, что найденные результаты относятся к математике
        math_results = [r for r in data['results'] if r['type'] == 'math']
        self.assertGreater(len(math_results), 0)

    def test_focused_search_russian(self):
        """Тест: фокусированный поиск по русскому языку"""
        response = self.client.get(reverse('learning:focused_search'), {'q': 'сочинение'})

        self.assertEqual(response.status_code, 200) # type: ignore

        data = json.loads(response.content) # type: ignore
        self.assertGreater(len(data['results']), 0) # type: ignore

        # Проверяем, что найденные результаты относятся к русскому языку
        russian_results = [r for r in data['results'] if r['type'] == 'russian']
        self.assertGreater(len(russian_results), 0)

    def test_subject_statistics(self):
        """Тест: статистика по предметам"""
        response = self.client.get(reverse('learning:subject_statistics'))

        self.assertEqual(response.status_code, 200) # type: ignore

        data = json.loads(response.content) # type: ignore

        # Проверяем структуру ответа
        self.assertIn('math', data)
        self.assertIn('russian', data)

        # Проверяем данные по математике
        self.assertEqual(data['math']['subjects_count'], 3)  # 3 варианта математики
        self.assertGreater(data['math']['total_tasks'], 0)

        # Проверяем данные по русскому языку
        self.assertEqual(data['russian']['subjects_count'], 2)  # 2 варианта русского языка
        self.assertGreater(data['russian']['total_tasks'], 0) # type: ignore

class AIPriorityManagerTestCase(TestCase):
    """Тесты системы приоритетов ИИ"""

    def setUp(self):
        self.priority_manager = AIPriorityManager()

    def test_math_question_analysis(self):
        """Тест: анализ вопроса по математике"""
        question = "Как решить квадратное уравнение x² - 5x + 6 = 0?"

        analysis = self.priority_manager.analyze_question(question)

        self.assertEqual(analysis['subject'], 'математика')
        self.assertEqual(analysis['priority'], 'high')
        self.assertIn('математика', analysis['prompt'].lower())

    def test_russian_question_analysis(self):
        """Тест: анализ вопроса по русскому языку"""
        question = "Как написать сочинение по русскому языку?"

        analysis = self.priority_manager.analyze_question(question)

        self.assertEqual(analysis['subject'], 'русский')
        self.assertEqual(analysis['priority'], 'high')
        self.assertIn('русский', analysis['prompt'].lower())

    def test_physics_question_analysis(self):
        """Тест: анализ вопроса по физике (вторичный предмет)"""
        question = "Что такое сила тяжести?"

        analysis = self.priority_manager.analyze_question(question)

        self.assertEqual(analysis['subject'], 'unknown')
        self.assertEqual(analysis['priority'], 'medium')
        self.assertIn('специализируюсь', analysis['prompt'].lower())

    def test_high_priority_response_config(self):
        """Тест: конфигурация ответа высокого приоритета"""
        config = self.priority_manager._get_response_config('high')

        self.assertTrue(config['include_examples'])
        self.assertTrue(config['include_steps'])
        self.assertTrue(config['include_tips'])
        self.assertTrue(config['use_formulas'])
        self.assertEqual(config['max_length'], 2000)

    def test_low_priority_response_config(self):
        """Тест: конфигурация ответа низкого приоритета"""
        config = self.priority_manager._get_response_config('low')

        self.assertFalse(config['include_examples'])
        self.assertFalse(config['include_steps'])
        self.assertTrue(config['redirect'])
        self.assertEqual(config['max_length'], 500)

    def test_redirect_message(self):
        """Тест: сообщение для перенаправления"""
        message = self.priority_manager.get_redirect_message('физика')

        self.assertIn('математика', message.lower())
        self.assertIn('русский', message.lower())
        self.assertIn('физика', message.lower())

class FIPIMonitorTestCase(TestCase):
    """Тесты мониторинга ФИПИ"""

    def setUp(self):
        self.monitor = FIPIMonitor()

    def test_subject_detection(self):
        """Тест: определение предмета по ключевым словам"""
        math_question = "Как решить уравнение?"
        russian_question = "Как написать сочинение?"
        unknown_question = "Что такое погода?"

        self.assertEqual(self.monitor._detect_subject(math_question), 'математика') # type: ignore
        self.assertEqual(self.monitor._detect_subject(russian_question), 'русский') # type: ignore
        self.assertEqual(self.monitor._detect_subject(unknown_question), 'unknown') # type: ignore

    def test_exam_type_detection(self):
        """Тест: определение типа экзамена"""
        ege_question = "Задача по математике ЕГЭ"
        oge_question = "Задание по русскому языку ОГЭ"
        unknown_question = "Просто вопрос"

        self.assertEqual(self.monitor._detect_exam_type(ege_question), 'ege') # type: ignore
        self.assertEqual(self.monitor._detect_exam_type(oge_question), 'oge') # type: ignore
        self.assertEqual(self.monitor._detect_exam_type(unknown_question), 'unknown') # type: ignore

    def test_priority_detection(self):
        """Тест: определение приоритета"""
        self.assertEqual(self.monitor._get_priority('математика', 'ege'), 'high') # type: ignore
        self.assertEqual(self.monitor._get_priority('русский', 'oge'), 'high') # type: ignore
        self.assertEqual(self.monitor._get_priority('физика', 'ege'), 'low') # type: ignore
        self.assertEqual(self.monitor._get_priority('unknown', 'ege'), 'medium') # type: ignore

    def test_prompt_selection(self):
        """Тест: выбор промпта"""
        math_ege_prompt = self.monitor._get_prompt('математика', 'ege') # type: ignore
        math_oge_prompt = self.monitor._get_prompt('математика', 'oge') # type: ignore
        russian_ege_prompt = self.monitor._get_prompt('русский', 'ege') # type: ignore
        redirect_prompt = self.monitor._get_prompt('unknown', 'ege') # type: ignore

        self.assertIn('математика', math_ege_prompt.lower())
        self.assertIn('математика', math_oge_prompt.lower())
        self.assertIn('русский', russian_ege_prompt.lower())
        self.assertIn('специализируюсь', redirect_prompt.lower())

class IntegrationTestCase(TestCase):
    """Интеграционные тесты"""

    def setUp(self):
        self.client = Client()

        # Создаем основные предметы
        self.math_prof = Subject.objects.create( # type: ignore
            name='Математика (профильная)',
            code='math_pro',
            exam_type='ЕГЭ',
            is_primary=True
        )

        self.russian_ege = Subject.objects.create( # type: ignore
            name='Русский язык (ЕГЭ)',
            code='russian_ege',
            exam_type='ЕГЭ',
            is_primary=True
        )

    def test_full_workflow(self):
        """Тест: полный рабочий процесс"""
        # 1. Заходим на главную страницу
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200) # type: ignore

        # 2. Переходим к списку предметов
        response = self.client.get(reverse('learning:subjects_list'))
        self.assertEqual(response.status_code, 200) # type: ignore

        # 3. Ищем по математике
        response = self.client.get(reverse('learning:focused_search'), {'q': 'математика'})
        self.assertEqual(response.status_code, 200) # type: ignore

        # 4. Получаем статистику
        response = self.client.get(reverse('learning:subject_statistics'))
        self.assertEqual(response.status_code, 200) # type: ignore

        data = json.loads(response.content) # type: ignore
        self.assertIn('math', data)
        self.assertIn('russian', data)

    def test_mobile_responsiveness(self):
        """Тест: мобильная адаптивность"""
        # Симулируем мобильный браузер
        response = self.client.get(
            reverse('learning:subjects_list'),
            HTTP_USER_AGENT='Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)'
        )

        self.assertEqual(response.status_code, 200) # type: ignore
        # Проверяем, что страница загружается на мобильном устройстве
        self.assertContains(response, 'subjects-grid')

    def test_performance(self):
        """Тест: производительность"""
        import time

        start_time = time.time()
        response = self.client.get(reverse('learning:subjects_list'))
        load_time = time.time() - start_time

        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertLess(load_time, 2.0)  # Менее 2 секунд

        start_time = time.time()
        response = self.client.get(reverse('learning:focused_search'), {'q': 'тест'})
        search_time = time.time() - start_time

        self.assertEqual(response.status_code, 200) # type: ignore  
        self.assertLess(search_time, 1.0)  # Менее 1 секунды
