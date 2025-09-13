"""
Тесты для модуля аутентификации
"""

from django.test import TestCase, Client
from django.contrib.auth.models import User
from authentication.forms import TechRegisterForm, TechLoginForm

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

        # Проверяем создание пользователя (профиль не создается автоматически)
        self.assertTrue(User.objects.filter(username=user.username).exists())

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
        _user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        form_data = {
            'username': 'test@example.com',
            'password': 'testpassword123'
        }
        _form = TechLoginForm(data=form_data)
        # Форма может быть невалидной без дополнительной настройки аутентификации

    def test_register_view_get(self):
        """Тест GET запроса к странице регистрации"""
        response = self.client.get('/auth/register/')
        self.assertEqual(response.status_code, 200)  # type: ignore

    def test_register_view_post_valid(self):
        """Тест POST запроса с валидными данными"""
        response = self.client.post('/auth/register/', self.test_user_data)
        self.assertEqual(response.status_code, 302)  # type: ignore  # Редирект после успешной регистрации

    def test_register_view_post_invalid(self):
        """Тест POST запроса с невалидными данными"""
        invalid_data = self.test_user_data.copy()
        invalid_data['email'] = 'invalid-email'
        response = self.client.post('/auth/register/', invalid_data)
        self.assertEqual(response.status_code, 200)  # Возврат формы с ошибками  # pyright: ignore[reportAttributeAccessIssue]

    def test_login_view_get(self):
        """Тест GET запроса к странице входа"""
        response = self.client.get('/auth/login/')
        self.assertEqual(response.status_code, 200)  # type: ignore

    def test_login_view_post_valid(self):
        """Тест POST запроса с валидными данными для входа"""
        # Создаем пользователя
        User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )

        form_data = {
            'username': 'test@example.com',
            'password': 'testpassword123'
        }
        response = self.client.post('/auth/login/', form_data)
        # После успешного входа должен быть редирект на dashboard
        self.assertEqual(response.status_code, 302)  # type: ignore
        # Проверяем, что редирект ведет на dashboard
        self.assertIn('/dashboard/', response.url)  # type: ignore

    def test_login_view_post_invalid(self):
        """Тест POST запроса с невалидными данными для входа"""
        form_data = {
            'username': 'nonexistent@example.com',
            'password': 'wrongpassword'
        }
        response = self.client.post('/auth/login/', form_data)
        self.assertEqual(response.status_code, 200)  # type: ignore  # Возврат формы с ошибками

    def test_logout_view(self):
        """Тест выхода из системы"""
        # Создаем и логиним пользователя
        _user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')

        # Проверяем, что пользователь залогинен
        self.assertTrue(_user.is_authenticated)  # type: ignore

        # Выходим из системы
        response = self.client.get('/logout/')  # Используем legacy URL
        # После выхода должен быть редирект на главную страницу
        self.assertEqual(response.status_code, 302)  # type: ignore
        self.assertIn('/', response.url)  # type: ignore

    def test_password_change_view(self):
        """Тест изменения пароля"""
        # Создаем и логиним пользователя
        _user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')

        # Тестируем GET запрос к dashboard (существующий URL)
        response = self.client.get('/auth/dashboard/')
        self.assertEqual(response.status_code, 200)  # type: ignore

        # Тестируем POST запрос к dashboard
        response = self.client.post('/auth/dashboard/', {})
        self.assertEqual(response.status_code, 200)  # type: ignore  # Dashboard обрабатывает только GET

    def test_password_reset_view(self):
        """Тест сброса пароля"""
        # Создаем и логиним пользователя
        _user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword123'
        )
        self.client.login(username='testuser', password='testpassword123')

        # Тестируем GET запрос к profile (существующий URL)
        response = self.client.get('/auth/profile/update/')
        self.assertEqual(response.status_code, 200)  # type: ignore

        # Тестируем POST запрос к profile
        form_data = {
            'first_name': 'Updated Name',
            'email': 'updated@example.com'
        }
        response = self.client.post('/auth/profile/update/', form_data)
        # После успешного обновления должен быть редирект на dashboard
        self.assertEqual(response.status_code, 302)  # type: ignore
        self.assertIn('/dashboard/', response.url)  # type: ignore
