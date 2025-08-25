"""
Модели для приложения core
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class Subject(models.Model):
    """Модель предмета"""
    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=10, unique=True, verbose_name="Код предмета")
    exam_type = models.CharField(max_length=20, choices=[
        ('ege', 'ЕГЭ'),
        ('oge', 'ОГЭ'),
    ], verbose_name="Тип экзамена")
    description = models.TextField(blank=True, verbose_name="Описание")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display()})"  # type: ignore

    @property
    def task_count(self):
        """Количество задач по предмету"""
        return self.task_set.count()  # type: ignore


class Task(models.Model):
    """Модель задачи"""
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Предмет")
    title = models.CharField(max_length=200, verbose_name="Название")
    text = models.TextField(verbose_name="Текст задачи")
    solution = models.TextField(blank=True, verbose_name="Решение")
    answer = models.CharField(max_length=100, blank=True, verbose_name="Ответ")
    difficulty = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=3,  # type: ignore
        verbose_name="Сложность"
    )
    source = models.CharField(max_length=100, blank=True, verbose_name="Источник")
    year = models.IntegerField(blank=True, null=True, verbose_name="Год")
    topics = models.JSONField(default=list, blank=True, verbose_name="Темы")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['subject', 'difficulty', 'title']

    def __str__(self):
        return f"{self.subject.name}: {self.title}"


class UserProgress(models.Model):
    """Модель прогресса пользователя по задаче"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name='core_userprogress_set')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача")
    is_correct = models.BooleanField(default=False, verbose_name="Правильно решено")  # type: ignore
    attempts = models.IntegerField(default=1, verbose_name="Количество попыток")  # type: ignore
    time_spent = models.IntegerField(default=0, verbose_name="Время в секундах")  # type: ignore
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Последняя попытка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"
        unique_together = ['user', 'task']
        ordering = ['-last_attempt']

    def __str__(self):
        return f"{self.user.username} - {self.task.title}"  # type: ignore
