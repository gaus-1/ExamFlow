from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class UserThemePreference(models.Model):
    """
    Модель для хранения предпочтений пользователя по дизайну

    Поля:
    - user: связь с пользователем (один к одному)
    - theme: выбранная тема (school/adult)
    - created_at: дата создания записи
    - updated_at: дата последнего обновления
    - is_active: активна ли тема
    """

    THEME_CHOICES = [
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='theme_preference',
        verbose_name='Пользователь'
    )

    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default='school',
        verbose_name='Выбранная тема'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    is_active = models.BooleanField(
        default=True,
        verbose_name='Тема активна'
    )

    class Meta:
        verbose_name = 'Предпочтение по дизайну'
        verbose_name_plural = 'Предпочтения по дизайну'
        db_table = 'themes_user_theme_preference'
        ordering = ['-updated_at']

    def __str__(self):
        return "Тема пользователя {self.user.username}: {self.get_theme_display()}"

    def get_theme_display_name(self):
        """Получение читаемого названия темы"""
        return dict(self.THEME_CHOICES).get(self.theme, 'Неизвестно')

    def switch_theme(self, new_theme):
        """Переключение на новую тему"""
        if new_theme in dict(self.THEME_CHOICES):
            self.theme = new_theme
            self.save()
            return True
        return False

class ThemeUsage(models.Model):
    """
    Модель для отслеживания использования тем пользователями

    Поля:
    - user: пользователь
    - theme: использованная тема
    - session_duration: продолжительность сессии в секундах
    - page_views: количество просмотренных страниц
    - created_at: дата создания записи
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='theme_usage',
        verbose_name='Пользователь'
    )

    theme = models.CharField(
        max_length=10,
        choices=UserThemePreference.THEME_CHOICES,
        verbose_name='Использованная тема'
    )

    session_duration = models.PositiveIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(86400)],  # Максимум 24 часа
        verbose_name='Продолжительность сессии (секунды)'
    )

    page_views = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество просмотренных страниц'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    class Meta:
        verbose_name = 'Использование темы'
        verbose_name_plural = 'Использование тем'
        db_table = 'themes_theme_usage'
        ordering = ['-created_at']

    def __str__(self):
        return "Использование темы {self.theme} пользователем {self.user.username}"

    def get_session_duration_minutes(self):
        """Получение продолжительности сессии в минутах"""
        return round(self.session_duration / 60, 1)

    def get_session_duration_hours(self):
        """Получение продолжительности сессии в часах"""
        return round(self.session_duration / 3600, 2)

class ThemeCustomization(models.Model):
    """
    Модель для пользовательских настроек темы

    Поля:
    - user: пользователь
    - theme: базовая тема
    - custom_colors: JSON с пользовательскими цветами
    - custom_fonts: JSON с пользовательскими шрифтами
    - is_active: активны ли пользовательские настройки
    """

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='theme_customizations',
        verbose_name='Пользователь'
    )

    theme = models.CharField(
        max_length=10,
        choices=UserThemePreference.THEME_CHOICES,
        verbose_name='Базовая тема'
    )

    custom_colors = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Пользовательские цвета'
    )

    custom_fonts = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='Пользовательские шрифты'
    )

    is_active = models.BooleanField(
        default=False,
        verbose_name='Пользовательские настройки активны'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )

    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        verbose_name = 'Пользовательская настройка темы'
        verbose_name_plural = 'Пользовательские настройки тем'
        db_table = 'themes_theme_customization'
        ordering = ['-updated_at']
        unique_together = ['user', 'theme']

    def __str__(self):
        return "Пользовательские настройки темы {self.theme} для {self.user.username}"

    def get_custom_color(self, color_name, default_color):
        """Получение пользовательского цвета или значения по умолчанию"""
        return self.custom_colors.get(color_name, default_color)

    def get_custom_font(self, font_name, default_font):
        """Получение пользовательского шрифта или значения по умолчанию"""
        return self.custom_fonts.get(font_name, default_font)

    def has_customizations(self):
        """Проверка наличия пользовательских настроек"""
        return bool(self.custom_colors or self.custom_fonts)
