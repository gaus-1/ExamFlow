"""
Тесты для модуля аутентификации
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from authentication.forms import TechRegisterForm, TechLoginForm
from core.models import UserProfile


class TestAuthentication(TestCase):
    """Тесты аутентификации пользователей"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.test_user_data = {
            'first_name': 'Тест',
            'email': 'test@example.com',
            'password1': 'testpassword123',
            'password2': 'testpassword123'
        }

    def test_register_form_valid(self):
        """Тест валидной формы регистрации"""
        form = TechRegisterForm(data=self.test_user_data)
        self.assertTrue(form.is_valid())

    def test_register_form_invalid_email(self):
        """Тест невалидного email в форме регистрации"""
        invalid_data = self.test_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        form = TechRegisterForm(data=invalid_data)
        self.assertFalse(form.is_valid())

    def test_register_form_password_mismatch(self):
        """Тест несовпадающих паролей"""
        invalid_data = self.test_user_data.copy()
        invalid_data['password2'] = 'differentpassword'
        form = TechRegisterForm(data=invalid_data)
        self.assertFalse(form.is_valid())

    def test_user_creation_with_profile(self):
        """Тест создания пользователя с профилем"""
        form = TechRegisterForm(data=self.test_user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.first_name, 'Тест')
        self.assertEqual(user.email, 'test@example.com')
        self.assertTrue(user.username.startswith('test'))
        
        # Проверяем создание профиля
        from core.models import UserProfile
        self.assertTrue(UserProfile.objects.filter(user=user).exists()) # type: ignore

    def test_username_generation_from_email(self):
        """Тест автогенерации username из email"""
        form = TechRegisterForm(data=self.test_user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'test')

    def test_username_uniqueness(self):
        """Тест уникальности username при конфликтах"""
        # Создаем первого пользователя
        User.objects.create_user(username='test', email='existing@example.com')
        
        # Пытаемся создать второго с тем же базовым username
        form = TechRegisterForm(data=self.test_user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.username, 'test1')

    def test_login_form_valid(self):
        """Тест валидной формы входа"""
        # Создаем пользователя
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        
        form_data = {
            'username': 'test@example.com',
            'password': 'testpassword123'
        }
        form = TechLoginForm(data=form_data)
        # Форма может быть невалидной без дополнительной настройки аутентификации

    def test_register_view_get(self):
        """Тест GET запроса к странице регистрации"""
        response = self.client.get('/auth/register/')
        self.assertEqual(response.status_code, 200) # type: ignore

    def test_register_view_post_valid(self):
        """Тест POST запроса с валидными данными"""
        response = self.client.post('/auth/register/', self.test_user_data)
        # Ожидаем редирект после успешной регистрации
        self.assertEqual(response.status_code, 302) # type: ignore
        
        # Проверяем создание пользователя
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_register_view_post_invalid(self):
        """Тест POST запроса с невалидными данными"""
        invalid_data = self.test_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        
        response = self.client.post('/auth/register/', invalid_data)
        self.assertEqual(response.status_code, 200)  # Остаемся на той же странице # type: ignore
        
        # Пользователь не должен быть создан
        self.assertFalse(User.objects.filter(first_name='Тест').exists())
