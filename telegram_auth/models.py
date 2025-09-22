"""
Модели для Telegram аутентификации ExamFlow
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils import timezone


class TelegramUserManager(BaseUserManager):
    """Кастомный менеджер для TelegramUser"""
    
    def create_user(self, telegram_id, **extra_fields):
        """Создает обычного пользователя"""
        if not telegram_id:
            raise ValueError('Telegram ID обязателен')
        
        user = self.model(telegram_id=telegram_id, **extra_fields)
        user.set_unusable_password()
        user.save(using=self._db)
        return user
    
    def create_superuser(self, telegram_id, **extra_fields):
        """Создает суперпользователя"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Суперпользователь должен иметь is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Суперпользователь должен иметь is_superuser=True')
        
        return self.create_user(telegram_id, **extra_fields)


class TelegramUser(AbstractUser):
    """Пользователь с Telegram аутентификацией"""
    
    # Кастомный менеджер
    objects = TelegramUserManager()

    # Убираем стандартные поля Django User, которые нам не нужны
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(blank=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)

    # Telegram поля
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram Username"
    )
    telegram_first_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram First Name"
    )
    telegram_last_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Telegram Last Name"
    )

    # Дополнительные поля
    avatar_url = models.URLField(blank=True, verbose_name="Avatar URL")
    language_code = models.CharField(
        max_length=10,
        default='ru',
        verbose_name="Language Code"
    )

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Updated At")
    last_login = models.DateTimeField(null=True, blank=True, verbose_name="Last Login")

    # Настройки пользователя
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    is_premium = models.BooleanField(default=False, verbose_name="Is Premium")

    # Используем telegram_id как уникальное поле для входа
    USERNAME_FIELD = 'telegram_id'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = "Telegram User"
        verbose_name_plural = "Telegram Users"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.telegram_first_name} (@{self.telegram_username})" if self.telegram_username else f"User {self.telegram_id}"

    @property
    def display_name(self):
        """Получает отображаемое имя пользователя"""
        if self.telegram_first_name:
            if self.telegram_last_name:
                return f"{self.telegram_first_name} {self.telegram_last_name}"
            return self.telegram_first_name
        return f"User {self.telegram_id}"

    @property
    def full_username(self):
        """Получает полный username"""
        return f"@{self.telegram_username}" if self.telegram_username else None


class TelegramAuthSession(models.Model):
    """Сессия аутентификации через Telegram"""

    user = models.ForeignKey(
        TelegramUser,
        on_delete=models.CASCADE,
        related_name='auth_sessions',
        verbose_name="User"
    )
    session_token = models.CharField(
        max_length=255,
        unique=True,
        verbose_name="Session Token"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    expires_at = models.DateTimeField(verbose_name="Expires At")
    is_active = models.BooleanField(default=True, verbose_name="Is Active")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")

    class Meta:
        verbose_name = "Telegram Auth Session"
        verbose_name_plural = "Telegram Auth Sessions"
        ordering = ['-created_at']

    def __str__(self):
        return f"Session for {self.user.display_name} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"

    @property
    def is_expired(self):
        """Проверяет, истекла ли сессия"""
        return timezone.now() > self.expires_at


class TelegramAuthLog(models.Model):
    """Лог попыток аутентификации через Telegram"""

    telegram_id = models.BigIntegerField(verbose_name="Telegram ID")
    success = models.BooleanField(verbose_name="Success")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP Address")
    user_agent = models.TextField(blank=True, verbose_name="User Agent")
    error_message = models.TextField(blank=True, verbose_name="Error Message")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")

    class Meta:
        verbose_name = "Telegram Auth Log"
        verbose_name_plural = "Telegram Auth Logs"
        ordering = ['-created_at']

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"Auth {status} for {self.telegram_id} ({self.created_at.strftime('%d.%m.%Y %H:%M')})"
