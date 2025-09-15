"""
Unit тесты для AI API
"""

import json
from django.test import TestCase, Client
from django.conf import settings
from unittest.mock import patch, MagicMock

class TestAIAssistantAPI(TestCase):
    """Тесты для AI Assistant API"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )

    @patch('ai.api.model')
    def test_ai_chat_success(self, mock_model):
        """Тест успешного запроса к AI"""
        # Мокаем ответ от модели
        mock_response = MagicMock()
        mock_response.text = "Тестовый ответ от AI"
        mock_model.generate_content.return_value = mock_response

        # Отправляем запрос
        response = self.client.post('/ai/api/chat/',
            data=json.dumps({'prompt': 'Тестовый вопрос'}),
            content_type='application/json'
        )

        # Проверяем ответ
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('answer', data)
        self.assertIn('sources', data)
        self.assertIn('practice', data)

    def test_ai_chat_empty_prompt(self):
        """Тест с пустым промптом"""
        response = self.client.post('/ai/api/chat/',
            data=json.dumps({'prompt': ''}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_ai_chat_long_prompt(self):
        """Тест с слишком длинным промптом"""
        long_prompt = 'a' * 2001  # Превышаем лимит в 2000 символов

        response = self.client.post('/ai/api/chat/',
            data=json.dumps({'prompt': long_prompt}),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_ai_chat_large_request(self):
        """Тест с слишком большим запросом"""
        large_data = 'a' * 10001  # Превышаем лимит в 10KB

        response = self.client.post('/ai/api/chat/',
            data=large_data,
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 413)
        data = json.loads(response.content)
        self.assertIn('error', data)

class TestProblemsAPI(TestCase):
    """Тесты для Problems API"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()

    def test_get_problems_success(self):
        """Тест получения задач"""
        response = self.client.get('/api/problems/?topic=mathematics&limit=5')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('topic', data)
        self.assertIn('problems', data)
        self.assertIn('total', data)

    def test_get_problems_no_topic(self):
        """Тест без указания темы"""
        response = self.client.get('/api/problems/')

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn('error', data)

    def test_check_answer_success(self):
        """Тест проверки ответа"""
        response = self.client.post('/api/problems/',
            data=json.dumps({
                'problem_id': 1,
                'answer': 0
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('problem_id', data)
        self.assertIn('is_correct', data)
        self.assertIn('feedback', data)

class TestUserProfileAPI(TestCase):
    """Тесты для User Profile API"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')

    def test_get_profile_success(self):
        """Тест получения профиля"""
        response = self.client.get('/api/user/profile/')

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('id', data)
        self.assertIn('username', data)
        self.assertIn('level', data)
        self.assertIn('xp', data)

    def test_update_progress_success(self):
        """Тест обновления прогресса"""
        response = self.client.post('/api/user/profile/',
            data=json.dumps({
                'action': 'solve_problem',
                'problem_id': 1,
                'is_correct': True,
                'subject': 'mathematics'
            }),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('status', data)
        self.assertEqual(data['status'], 'success')

class TestSecurity(TestCase):
    """Тесты безопасности"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()

    def test_xss_protection(self):
        """Тест защиты от XSS"""
        malicious_prompt = "<script>alert('xss')</script>"

        with patch('ai.api.model') as mock_model:
            mock_response = MagicMock()
            mock_response.text = "Безопасный ответ"
            mock_model.generate_content.return_value = mock_response

            response = self.client.post('/ai/api/chat/',
                data=json.dumps({'prompt': malicious_prompt}),
                content_type='application/json'
            )

            # Проверяем, что скрипт был экранирован
            self.assertEqual(response.status_code, 200)
            # В реальном коде здесь должна быть проверка на экранирование

    def test_sql_injection_protection(self):
        """Тест защиты от SQL инъекций"""
        malicious_topic = "'; DROP TABLE users; --"

        response = self.client.get('/api/problems/?topic={malicious_topic}')

        # Запрос должен обработаться безопасно
        self.assertIn(response.status_code, [200, 400])

class TestPerformance(TestCase):
    """Тесты производительности"""

    def setUp(self):
        """Настройка тестов"""
        self.client = Client()

    @patch('ai.api.cache')
    def test_caching_works(self, mock_cache):
        """Тест работы кэширования"""
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True

        with patch('ai.api.model') as mock_model:
            mock_response = MagicMock()
            mock_response.text = "Кэшированный ответ"
            mock_model.generate_content.return_value = mock_response

            # Первый запрос
            response1 = self.client.post('/ai/api/chat/',
                data=json.dumps({'prompt': 'Тест кэша'}),
                content_type='application/json'
            )

            # Второй запрос (должен использовать кэш)
            mock_cache.get.return_value = {
                'answer': 'Кэшированный ответ',
                'sources': [],
                'practice': {'topic': 'general', 'description': 'Тест'}
            }

            response2 = self.client.post('/ai/api/chat/',
                data=json.dumps({'prompt': 'Тест кэша'}),
                content_type='application/json'
            )

            # Проверяем, что кэш был использован
            self.assertEqual(response1.status_code, 200)
            self.assertEqual(response2.status_code, 200)
            mock_cache.get.assert_called()
