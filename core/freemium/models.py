"""
Модели для FREEMIUM системы ExamFlow 2.0
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserSubscription(models.Model):
    """Подписка пользователя"""
    
    SUBSCRIPTION_TYPES = [
        ('free', 'Бесплатный'),
        ('premium', 'Подписка'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscription')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPES, default='free')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True) # type: ignore
    
    class Meta:
        verbose_name = 'Подписка пользователя'
        verbose_name_plural = 'Подписки пользователей'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()}" # type: ignore
    
    @property
    def is_premium(self):
        """Проверка премиум статуса"""
        return self.subscription_type == 'premium' and self.is_active
    
    @property
    def is_expired(self):
        """Проверка истечения подписки"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at


class DailyUsage(models.Model):
    """Ежедневное использование ИИ"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='daily_usage')
    date = models.DateField(default=timezone.now)
    ai_requests_count = models.PositiveIntegerField(default=0) # type: ignore
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Ежедневное использование'
        verbose_name_plural = 'Ежедневное использование'
        unique_together = ['user', 'date']
    
    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.ai_requests_count} запросов" # type: ignore
    
    @classmethod
    def get_today_usage(cls, user):
        """Получить использование за сегодня"""
        today = timezone.now().date()
        usage, created = cls.objects.get_or_create( # type: ignore
            user=user,
            date=today,
            defaults={'ai_requests_count': 0}
        )
        return usage
    
    def can_make_request(self):
        """Проверка возможности сделать запрос"""
        # Проверяем подписку
        if hasattr(self.user, 'subscription') and self.user.subscription.is_premium: # type: ignore
            return True
        
        # Для бесплатного тарифа - максимум 10 запросов в день
        return self.ai_requests_count < 10 # type: ignore
    
    def increment_usage(self):
        """Увеличить счетчик использования"""
        if self.can_make_request():
            self.ai_requests_count += 1 # type: ignore
            self.save()
            return True
        return False


class SubscriptionLimit(models.Model):
    """Лимиты подписок"""
    
    subscription_type = models.CharField(max_length=20, choices=UserSubscription.SUBSCRIPTION_TYPES, unique=True)
    daily_ai_requests = models.PositiveIntegerField(default=10) # type: ignore
    max_subjects = models.PositiveIntegerField(default=0)  # 0 = без ограничений # type: ignore
    has_priority_support = models.BooleanField(default=False) # type: ignore
    has_advanced_analytics = models.BooleanField(default=False) # type: ignore
    has_exclusive_content = models.BooleanField(default=False) # type: ignore
    has_personal_curator = models.BooleanField(default=False) # type: ignore
    has_advanced_analytics = models.BooleanField(default=False) # type: ignore
    has_exclusive_content = models.BooleanField(default=False) # type: ignore
    has_personal_curator = models.BooleanField(default=False) # type: ignore
    
    class Meta:
        verbose_name = 'Лимит подписки'
        verbose_name_plural = 'Лимиты подписок'
    
    def __str__(self):
        return f"Лимиты для {self.get_subscription_type_display()}" # type: ignore
    
    @classmethod
    def get_limits(cls, subscription_type):
        """Получить лимиты для типа подписки"""
        limits, created = cls.objects.get_or_create( # type: ignore
            subscription_type=subscription_type,
            defaults={
                'daily_ai_requests': 10 if subscription_type == 'free' else 999999, # type: ignore
                'max_subjects': 0, # type: ignore   
                'has_priority_support': subscription_type == 'premium', # type: ignore
                'has_advanced_analytics': subscription_type == 'premium', # type: ignore
                'has_exclusive_content': subscription_type == 'premium', # type: ignore
                'has_personal_curator': subscription_type == 'premium', # type: ignore
            }
        )
        return limits
