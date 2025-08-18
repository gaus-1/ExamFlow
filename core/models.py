from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
import uuid

class ExamType(models.Model):
    name = models.CharField(max_length=50, verbose_name="Тип экзамена")
    code = models.CharField(max_length=10, verbose_name="Код")
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Тип экзамена"
        verbose_name_plural = "Типы экзаменов"

class Subject(models.Model):
    EXAM_TYPES = [
        ('ЕГЭ', 'Единый государственный экзамен'),
        ('ОГЭ', 'Основной государственный экзамен'),
    ]
    
    name = models.CharField(max_length=100, verbose_name="Название предмета")
    exam_type = models.CharField(max_length=3, choices=EXAM_TYPES, default='ЕГЭ', verbose_name="Тип экзамена")
    
    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
    
    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display()})"

class Topic(models.Model):
    name = models.CharField(max_length=200, verbose_name="Тема")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    code = models.CharField(max_length=20, verbose_name="Код темы")
    
    def __str__(self):
        return f"{self.subject.name} - {self.name}"
    
    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"

class Task(models.Model):
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")  # Оставляем blank=True, null=True
    difficulty = models.IntegerField(default=1, verbose_name="Сложность")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Дата создания")  # Оставляем default=timezone.now
    answer = models.TextField(blank=True, null=True, verbose_name="Ответ")
    source = models.CharField(max_length=200, blank=True, null=True, verbose_name="Источник")
    
    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"
    
    def __str__(self):
        return self.title

class UserProgress(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задание")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно решено")
    user_answer = models.TextField(blank=True, verbose_name="Ответ пользователя")
    attempts = models.IntegerField(default=0, verbose_name="Попыток")
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Последняя попытка")
    
    def __str__(self):
        return f"{self.user.username} - {self.task.subject.name}"
    
    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"


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
    daily_tasks_limit = models.IntegerField(default=5)  # Лимит заданий в день для бесплатных
    tasks_solved_today = models.IntegerField(default=0)
    
    def __str__(self):
        return f"Профиль: {self.user.username}"
    
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


class UserRating(TimeStampedModel):
    """Рейтинг пользователя"""
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    correct_answers = models.IntegerField(default=0)
    incorrect_answers = models.IntegerField(default=0)
    total_attempts = models.IntegerField(default=0)
    total_time_spent = models.IntegerField(default=0)  # Общее время в секундах
    rank = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-correct_answers', 'total_time_spent']
        verbose_name = "Рейтинг пользователя"
        verbose_name_plural = "Рейтинги пользователей"
    
    @property
    def accuracy(self):
        """Процент правильных ответов"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_answers / self.total_attempts) * 100, 1)
    
    def __str__(self):
        return f"{self.user.username}: {self.correct_answers}/{self.total_attempts} ({self.accuracy}%)"


class Achievement(TimeStampedModel):
    """Достижения пользователя"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon = models.CharField(max_length=50, default='fas fa-trophy')
    color = models.CharField(max_length=7, default='#ffd700')
    
    def __str__(self):
        return f"{self.user.username}: {self.name}"
    
    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"


class Subscription(TimeStampedModel):
    """Подписки пользователей"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    subscription_type = models.CharField(
        max_length=20,
        choices=[('monthly', 'Месячный'), ('yearly', 'Годовой')]
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_id = models.CharField(max_length=100, unique=True)
    payment_method = models.CharField(
        max_length=20,
        choices=[('card', 'Банковская карта'), ('btc', 'Bitcoin')]
    )
    status = models.CharField(
        max_length=20,
        choices=[('pending', 'Ожидает'), ('active', 'Активна'), ('expired', 'Истекла'), ('cancelled', 'Отменена')],
        default='pending'
    )
    starts_at = models.DateTimeField()
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"{self.user.username}: {self.subscription_type} ({self.status})"
    
    class Meta:
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"