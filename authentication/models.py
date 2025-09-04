"""
Модели для модуля аутентификации

Содержит модели для управления пользователями и подписками:
- UserProfile (расширенный профиль)
- Subscription (подписки пользователей)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Абстрактная модель с временными метками"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class UserProfile(TimeStampedModel):
    """Расширенный профиль пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    telegram_id = models.CharField(max_length=50, blank=True, unique=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    level = models.IntegerField(default=1)
    experience = models.IntegerField(default=0)
    streak_days = models.IntegerField(default=0)  # Дни подряд
    last_activity = models.DateTimeField(auto_now=True)
    subscription_type = models.CharField(
        max_length=20,
        choices=[('free', 'Бесплатный'), ('monthly', 'Месячный'), ('yearly', 'Годовой')],
        default='free'
    )
    subscription_expires = models.DateTimeField(null=True, blank=True)
    current_task_id = models.IntegerField(null=True, blank=True)
    daily_tasks_limit = models.IntegerField(default=5)
    tasks_solved_today = models.IntegerField(default=0)
    last_daily_reset = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Профиль {self.user.username}"

    @property
    def is_premium(self):
        """Проверяет, есть ли активная подписка"""
        if self.subscription_type == 'free':
            return False
        return self.subscription_expires and self.subscription_expires > timezone.now()

    @property
    def can_solve_tasks(self):
        """Может ли пользователь решать задания"""
        if self.is_premium:
            return True
        return self.tasks_solved_today < self.daily_tasks_limit

    def reset_daily_counter(self):
        """Сброс ежедневного счетчика заданий"""
        self.tasks_solved_today = 0
        self.save()

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"


class Subscription(TimeStampedModel):
    """Подписка пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь")
    subscription_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Месячный'), ('yearly', 'Годовой')],
        verbose_name="Тип подписки"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активна")
    start_date = models.DateTimeField(default=timezone.now, verbose_name="Дата начала")
    end_date = models.DateTimeField(verbose_name="Дата окончания")
    auto_renewal = models.BooleanField(default=True, verbose_name="Автопродление")

    def __str__(self):
        return f"Подписка {self.user.username} - {self.get_subscription_type_display()}"

    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"

    def is_expired(self):
        """Проверяет, истекла ли подписка"""
        return timezone.now() > self.end_date

    def days_remaining(self):
        """Возвращает количество дней до истечения подписки"""
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now()
        return delta.days
