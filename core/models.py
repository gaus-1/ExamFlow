from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

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