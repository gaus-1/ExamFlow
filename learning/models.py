"""
Модели для модуля обучения

Содержит основные модели для работы с образовательным контентом:
- Предметы (Subject)
- Темы (Topic)
- Задания (Task)
- Прогресс пользователей (UserProgress)
- Достижения (Achievement)
- Рейтинги (UserRating)
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ExamType(models.Model):
    """Тип экзамена (ЕГЭ/ОГЭ)"""
    name = models.CharField(max_length=50, verbose_name="Тип экзамена")
    code = models.CharField(max_length=10, verbose_name="Код")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Тип экзамена"
        verbose_name_plural = "Типы экзаменов"


class Subject(models.Model):
    """Предмет для изучения"""
    EXAM_TYPES = [
        ('ЕГЭ', 'Единый государственный экзамен'),
        ('ОГЭ', 'Основной государственный экзамен'),
    ]

    name = models.CharField(max_length=100, verbose_name="Название предмета")
    exam_type = models.CharField(
        max_length=3,
        choices=EXAM_TYPES,
        default='ЕГЭ',
        verbose_name="Тип экзамена")

    class Meta:
        verbose_name = "Предмет"
        verbose_name_plural = "Предметы"

    def __str__(self):
        return f"{self.name} ({self.get_exam_type_display()})"  # type: ignore


class Topic(models.Model):
    """Тема предмета"""
    name = models.CharField(max_length=200, verbose_name="Тема")
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name="Предмет")
    code = models.CharField(max_length=20, verbose_name="Код темы")

    def __str__(self):
        return f"{self.subject.name} - {self.name}"

    class Meta:
        verbose_name = "Тема"
        verbose_name_plural = "Темы"


class Task(models.Model):
    """Задание по предмету"""
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name="Предмет")
    title = models.CharField(max_length=200, verbose_name="Заголовок")
    description = models.TextField(blank=True, null=True, verbose_name="Описание")
    difficulty = models.IntegerField(verbose_name="Сложность")
    created_at = models.DateTimeField(
        default=timezone.now,
        verbose_name="Дата создания")
    answer = models.TextField(blank=True, null=True, verbose_name="Ответ")
    source = models.CharField(
        max_length=200,
        blank=True,
        null=True,
        verbose_name="Источник")

    class Meta:
        verbose_name = "Задание"
        verbose_name_plural = "Задания"

    def __str__(self):
        return self.title


class UserProgress(models.Model):
    """Прогресс пользователя по заданиям"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='learning_userprogress_set')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задание")
    is_correct = models.BooleanField(default=False,
                                     verbose_name="Правильно решено")  # type: ignore
    user_answer = models.TextField(blank=True, verbose_name="Ответ пользователя")
    attempts = models.IntegerField(default=0, verbose_name="Попыток")  # type: ignore
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Последняя попытка")

    def __str__(self):
        return f"{self.user.username} - {self.task.subject.name}"  # type: ignore

    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"


class UserRating(models.Model):
    """Рейтинг пользователя"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь")
    total_points = models.IntegerField(
        default=0, verbose_name="Общее количество очков")  # type: ignore
    correct_answers = models.IntegerField(
        default=0, verbose_name="Правильных ответов")  # type: ignore
    incorrect_answers = models.IntegerField(
        default=0, verbose_name="Неправильных ответов")  # type: ignore
    total_attempts = models.IntegerField(
        default=0, verbose_name="Всего попыток")  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    def __str__(self):
        # type: ignore
        return f"Рейтинг {self.user.username}: {self.total_points} очков"

    class Meta:
        verbose_name = "Рейтинг пользователя"
        verbose_name_plural = "Рейтинги пользователей"


class Achievement(models.Model):
    """Достижения пользователей"""
    name = models.CharField(max_length=100, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    icon = models.CharField(max_length=50, blank=True, verbose_name="Иконка")
    points_required = models.IntegerField(
        default=0, verbose_name="Требуемые очки")  # type: ignore
    users = models.ManyToManyField(
        User,
        through='UserAchievement',
        verbose_name="Пользователи")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"


class UserAchievement(models.Model):
    """Связь пользователя с достижением"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь")
    achievement = models.ForeignKey(
        Achievement,
        on_delete=models.CASCADE,
        verbose_name="Достижение")
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата получения")

    def __str__(self):
        return f"{self.user.username} - {self.achievement.name}"  # type: ignore

    class Meta:
        verbose_name = "Достижение пользователя"
        verbose_name_plural = "Достижения пользователей"
        unique_together = ['user', 'achievement']
