"""
Тесты для модуля управления дизайнами (themes)
"""

from django.test import TestCase, Client
from django.urls import reverse
from .models import UserThemePreference, ThemeUsage, ThemeCustomization

class ThemesModelsTest(TestCase):
    """Тесты для моделей модуля themes"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.user = User.objects.create_user( # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_user_theme_preference_creation(self):
        """Тест создания предпочтений темы пользователя"""
        preference = UserThemePreference.objects.create( # type: ignore
            user=self.user,
            theme='school'
        )

        self.assertEqual(preference.theme, 'school')
        self.assertEqual(preference.user, self.user)
        self.assertTrue(preference.is_active)

    def test_theme_usage_creation(self):
        """Тест создания статистики использования темы"""
        usage = ThemeUsage.objects.create( # type: ignore
            user=self.user,
            theme='adult',
            session_duration=3600,
            page_views=10
        )

        self.assertEqual(usage.theme, 'adult')
        self.assertEqual(usage.session_duration, 3600)
        self.assertEqual(usage.page_views, 10)

    def test_theme_customization_creation(self):
        """Тест создания пользовательских настроек темы"""
        customization = ThemeCustomization.objects.create( # type: ignore
            user=self.user,
            theme='school',
            custom_colors={'primary': '#FF0000'},
            custom_fonts={'main': 'Arial'}
        )

        self.assertEqual(customization.theme, 'school')
        self.assertEqual(customization.custom_colors['primary'], '#FF0000')
        self.assertEqual(customization.custom_fonts['main'], 'Arial')

class ThemesViewsTest(TestCase):
    """Тесты для представлений модуля themes"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.user = User.objects.create_user( # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_test_themes_page(self):
        """Тест доступности тестовой страницы дизайнов"""
        response = self.client.get(reverse('themes:test_themes'))
        self.assertEqual(response.status_code, 200) # type: ignore
        self.assertContains(response, 'Тестирование переключателя дизайнов')

    def test_get_current_theme_api(self):
        """Тест API получения текущей темы"""
        response = self.client.get(reverse('themes:get_current_theme'))
        self.assertEqual(response.status_code, 200) # type: ignore
        data = response.json() # type: ignore
        self.assertIn('theme', data)
        self.assertEqual(data['theme'], 'school')  # По умолчанию

    def test_preview_theme_api(self):
        """Тест API предварительного просмотра темы"""
        response = self.client.get(reverse('themes:preview_theme', args=['adult']))
        self.assertEqual(response.status_code, 200) # type: ignore
        data = response.json() # type: ignore
        self.assertIn('theme', data)
        self.assertEqual(data['theme'], 'adult')

    def test_switch_theme_api_unauthenticated(self):
        """Тест API переключения темы для неавторизованного пользователя"""
        response = self.client.post(
            reverse('themes:switch_theme'),
            data={'theme': 'adult'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200) # type: ignore
        data = response.json() # type: ignore
        self.assertIn('success', data)
        self.assertTrue(data['success'])

class ThemesIntegrationTest(TestCase):
    """Интеграционные тесты для модуля themes"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.user = User.objects.create_user( # type: ignore
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

    def test_theme_switching_workflow(self):
        """Тест полного процесса переключения темы"""
        # Авторизуемся
        self.client.login(username='testuser', password='testpass123')

        # 1. Получаем текущую тему
        response = self.client.get(reverse('themes:get_current_theme'))
        initial_theme = response.json()['theme'] # type: ignore

        # 2. Переключаемся на другую тему
        new_theme = 'adult' if initial_theme == 'school' else 'school'
        response = self.client.post(
            reverse('themes:switch_theme'),
            data={'theme': new_theme},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200) # type: ignore

        # 3. Проверяем, что тема изменилась
        response = self.client.get(reverse('themes:get_current_theme'))
        updated_theme = response.json()['theme'] # type: ignore
        self.assertEqual(updated_theme, new_theme)

    def test_theme_preference_persistence(self):
        """Тест сохранения предпочтений темы"""
        # Авторизуемся
        self.client.login(username='testuser', password='testpass123')

        # Переключаем тему
        response = self.client.post(
            reverse('themes:switch_theme'),
            data={'theme': 'adult'},
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200) # type: ignore

        # Проверяем, что предпочтение сохранилось в базе
        preference = UserThemePreference.objects.get(user=self.user) # type: ignore
        self.assertEqual(preference.theme, 'adult')

    def test_theme_usage_tracking(self):
        """Тест отслеживания использования тем"""
        # Авторизуемся
        self.client.login(username='testuser', password='testpass123')

        # Переключаем тему несколько раз
        themes = ['school', 'adult', 'school']
        for theme in themes:
            response = self.client.post(
                reverse('themes:switch_theme'),
                data={'theme': theme},
                content_type='application/json'
            )
            self.assertEqual(response.status_code, 200) # type: ignore

        # Проверяем, что создались записи об использовании
        usage_count = ThemeUsage.objects.filter(user=self.user).count() # type: ignore
        self.assertGreater(usage_count, 0)

class ThemesAdminTest(TestCase):
    """Тесты для административной панели модуля themes"""

    def setUp(self):
        """Настройка тестовых данных"""
        self.client = Client()
        self.admin_user = User.objects.create_superuser( # type: ignore
            username='admin',
            email='admin@example.com',
            password='adminpass123'
        )

    def test_admin_access(self):
        """Тест доступа к административной панели"""
        self.client.login(username='admin', password='adminpass123')

        # Проверяем доступ к списку предпочтений тем
        response = self.client.get('/admin/themes/userthemepreference/')
        self.assertEqual(response.status_code, 200) # type: ignore

        # Проверяем доступ к списку использования тем
        response = self.client.get('/admin/themes/themeusage/')
        self.assertEqual(response.status_code, 200) # type: ignore

        # Проверяем доступ к списку кастомизации тем
        response = self.client.get('/admin/themes/themecustomization/')
        self.assertEqual(response.status_code, 200) # type: ignore
