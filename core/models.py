"""
Основные модели для ExamFlow

Содержит только уникальные модели, которые не дублируются в других приложениях:
- ReminderLog (логи напоминаний)
- VoiceMessage (голосовые сообщения)
- FipiTask (задания из ФИПИ)
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


class ReminderLog(TimeStampedModel):
    """Логи отправленных напоминаний пользователям (чтобы не спамить).
    reminder_type: например, 'weekly_inactive'
    last_sent_at: когда в последний раз было отправлено напоминание данного типа.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    reminder_type = models.CharField(max_length=50, default='weekly_inactive')
    last_sent_at = models.DateTimeField(default=timezone.now)

    class Meta:
        verbose_name = "Лог напоминаний"
        verbose_name_plural = "Логи напоминаний"
        unique_together = ['user', 'reminder_type']
    
    def __str__(self):
        return f"{self.user.username} - {self.reminder_type} @ {self.last_sent_at.strftime('%Y-%m-%d %H:%M')}"


class VoiceMessage(TimeStampedModel):
    """Голосовые сообщения для заданий"""
    task_id = models.IntegerField(verbose_name="ID задания")
    audio_file = models.FileField(upload_to='voice_hints/', verbose_name="Аудио файл")
    duration = models.IntegerField(verbose_name="Длительность в секундах")
    is_active = models.BooleanField(default=True, verbose_name="Активно")
    
    class Meta:
        verbose_name = "Голосовое сообщение"
        verbose_name_plural = "Голосовые сообщения"
    
    def __str__(self):
        return f"Голосовая подсказка для задания {self.task_id}"


class FipiTask(TimeStampedModel):
    """Задания из ФИПИ (Федеральный институт педагогических измерений)"""
    subject = models.CharField(max_length=100, verbose_name="Предмет")
    exam_type = models.CharField(max_length=10, verbose_name="Тип экзамена")
    task_number = models.IntegerField(verbose_name="Номер задания")
    content = models.TextField(verbose_name="Содержание задания")
    answer = models.TextField(blank=True, null=True, verbose_name="Ответ")
    explanation = models.TextField(blank=True, null=True, verbose_name="Объяснение")
    source_url = models.URLField(blank=True, verbose_name="Источник")
    
    class Meta:
        verbose_name = "Задание ФИПИ"
        verbose_name_plural = "Задания ФИПИ"
        unique_together = ['subject', 'exam_type', 'task_number']
    
    def __str__(self):
        return f"{self.subject} {self.exam_type} - Задание {self.task_number}"