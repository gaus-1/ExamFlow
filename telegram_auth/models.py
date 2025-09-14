"""
Модели для Telegram аутентификации ExamFlow
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class TelegramUser(AbstractUser):
    """Пользователь с Telegram аутентификацией"""
    
    # Убираем стандартные поля Django User, которые нам не нужны
    username = None
    email = None
    first_name = None
    last_name = None
    
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
