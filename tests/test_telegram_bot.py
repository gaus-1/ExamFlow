"""
Тесты для Telegram бота
"""

import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from unittest.mock import Mock, patch
from telegram_bot.bot_handlers import get_or_create_user
from core.models import UserProfile, UserRating, Subject, Task, Topic, ExamType


class TestTelegramBot(TestCase):
    """Тесты Telegram бота"""

    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем тестовые данные для бота
        self.exam_type = ExamType.objects.create(
            name='ЕГЭ',
            description='Единый государственный экзамен'
        )
        
        self.subject = Subject.objects.create(
            name='Математика',
            exam_type=self.exam_type
        )
        
        self.topic = Topic.objects.create(
            name='Алгебра',
            subject=self.subject
        )
        
        self.task = Task.objects.create(
            title='Тестовое задание',
            content='Решите: 2 + 2 = ?',
            answer='4',
            topic=self.topic
        )

    def test_get_or_create_user_new(self):
        """Тест создания нового пользователя из Telegram"""
        # Создаем мок Telegram пользователя
        telegram_user = Mock()
        telegram_user.id = 123456789
        telegram_user.first_name = 'Тест'
        telegram_user.last_name = 'Пользователь'
        
        user, created = get_or_create_user(telegram_user)
        
        self.assertTrue(created)
        self.assertEqual(user.username, 'tg_123456789')
        self.assertEqual(user.first_name, 'Тест')
        self.assertEqual(user.last_name, 'Пользователь')
        
        # Проверяем создание профиля
        profile = UserProfile.objects.get(user=user)
        self.assertEqual(profile.telegram_id, '123456789')
        
        # Проверяем создание рейтинга
        self.assertTrue(UserRating.objects.filter(user=user).exists())

    def test_get_or_create_user_existing(self):
        """Тест получения существующего пользователя"""
        # Создаем пользователя заранее
        existing_user = User.objects.create_user(
            username='tg_123456789',
            first_name='Тест'
        )
        UserProfile.objects.create(
            user=existing_user,
            telegram_id='123456789'
        )
        
        telegram_user = Mock()
        telegram_user.id = 123456789
        telegram_user.first_name = 'Тест'
        telegram_user.last_name = 'Пользователь'
        
        user, created = get_or_create_user(telegram_user)
        
        self.assertFalse(created)
        self.assertEqual(user, existing_user)

    def test_telegram_user_without_last_name(self):
        """Тест пользователя без фамилии"""
        telegram_user = Mock()
        telegram_user.id = 987654321
        telegram_user.first_name = 'Тест'
        telegram_user.last_name = None
        
        user, created = get_or_create_user(telegram_user)
        
        self.assertTrue(created)
        self.assertEqual(user.first_name, 'Тест')
        self.assertEqual(user.last_name, '')

    def test_telegram_user_without_first_name(self):
        """Тест пользователя без имени"""
        telegram_user = Mock()
        telegram_user.id = 555666777
        telegram_user.first_name = None
        telegram_user.last_name = 'Пользователь'
        
        user, created = get_or_create_user(telegram_user)
        
        self.assertTrue(created)
        self.assertEqual(user.first_name, '')
        self.assertEqual(user.last_name, 'Пользователь')

    @patch('telegram_bot.views.get_bot')
    def test_webhook_view_valid_update(self, mock_get_bot):
        """Тест webhook с валидным обновлением"""
        from django.test import Client
        import json
        
        client = Client()
        
        # Мокаем бота
        mock_bot = Mock()
        mock_get_bot.return_value = mock_bot
        
        # Создаем тестовые данные webhook
        webhook_data = {
            'update_id': 123,
            'message': {
                'message_id': 456,
                'date': 1640995200,
                'chat': {
                    'id': 123456789,
                    'type': 'private'
                },
                'from': {
                    'id': 123456789,
                    'first_name': 'Тест'
                },
                'text': '/start'
            }
        }
        
        with patch('telegram_bot.views.handle_telegram_update') as mock_handle:
            response = client.post(
                '/bot/webhook/',
                data=json.dumps(webhook_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content.decode(), 'OK')

    def test_webhook_view_invalid_json(self):
        """Тест webhook с невалидным JSON"""
        from django.test import Client
        
        client = Client()
        
        response = client.post(
            '/bot/webhook/',
            data='invalid json',
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 500)

    def test_bot_api_status(self):
        """Тест API статуса бота"""
        from django.test import Client
        
        client = Client()
        response = client.get('/bot/api/status/')
        
        self.assertEqual(response.status_code, 200)
        
        import json
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'active')
        self.assertEqual(data['mode'], 'webhook')

    def test_bot_control_panel_unauthorized(self):
        """Тест панели управления ботом без авторизации"""
        from django.test import Client
        
        client = Client()
        response = client.get('/bot/control/')
        
        # Должен быть редирект на страницу входа
        self.assertEqual(response.status_code, 302)

    def test_bot_control_panel_authorized_superuser(self):
        """Тест панели управления ботом для суперпользователя"""
        from django.test import Client
        
        # Создаем суперпользователя
        superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )
        
        client = Client()
        client.login(username='admin', password='adminpass123')
        
        response = client.get('/bot/control/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Webhook режим')
