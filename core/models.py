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
    explanation = models.TextField(blank=True, verbose_name="Объяснение")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Задача"
        verbose_name_plural = "Задачи"
        ordering = ['subject', 'difficulty', 'title']

    def __str__(self):
        return f"{self.subject.name}: {self.title}"
    
    def check_answer(self, user_answer):
        """Проверяет правильность ответа пользователя"""
        if not self.answer:
            return False
        return str(user_answer).strip().lower() == str(self.answer).strip().lower()


class UserProgress(models.Model):
    """Модель прогресса пользователя по задаче"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Пользователь", related_name='core_userprogress_set')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача")
    user_answer = models.CharField(max_length=200, blank=True, verbose_name="Ответ пользователя")
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


class UnifiedProfile(models.Model):
    """Унифицированный профиль пользователя для сайта и бота"""
    
    # Основная информация
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь Django", null=True, blank=True)
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(max_length=100, blank=True, verbose_name="Telegram Username")
    
    # Профиль пользователя
    display_name = models.CharField(max_length=100, verbose_name="Отображаемое имя")
    avatar_url = models.URLField(blank=True, verbose_name="URL аватара")
    
    # Настройки
    preferred_subjects = models.ManyToManyField(Subject, blank=True, verbose_name="Предпочитаемые предметы")
    notification_settings = models.JSONField(default=dict, verbose_name="Настройки уведомлений")
    
    # Статистика и прогресс
    total_solved = models.IntegerField(default=0, verbose_name="Всего решено задач")  # type: ignore
    current_streak = models.IntegerField(default=0, verbose_name="Текущая серия")  # type: ignore
    best_streak = models.IntegerField(default=0, verbose_name="Лучшая серия")  # type: ignore
    
    # Gamification
    level = models.IntegerField(default=1, verbose_name="Уровень")  # type: ignore
    experience_points = models.IntegerField(default=0, verbose_name="Очки опыта")  # type: ignore
    achievements = models.JSONField(default=list, verbose_name="Достижения")
    
    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Последняя активность")
    
    class Meta:
        verbose_name = "Унифицированный профиль"
        verbose_name_plural = "Унифицированные профили"
        ordering = ['-last_activity']
    
    def __str__(self):
        return f"{self.display_name} (TG: {self.telegram_id})"
    
    @property
    def experience_to_next_level(self):
        """Опыт, необходимый для следующего уровня"""
        return (self.level * 100) - (self.experience_points % (self.level * 100))  # type: ignore
    
    def add_experience(self, points):
        """Добавляет опыт и проверяет повышение уровня"""
        self.experience_points += points
        new_level = (self.experience_points // 100) + 1
        if new_level > self.level:
            self.level = new_level
            return True  # Повышение уровня
        return False
    
    def add_achievement(self, achievement_id):
        """Добавляет достижение"""
        if achievement_id not in self.achievements:
            self.achievements.append(achievement_id)  # type: ignore
            self.save()
            return True
        return False


class DailyChallenge(models.Model):
    """Ежедневные вызовы"""
    
    CHALLENGE_TYPES = [
        ('solve_tasks', 'Решить задачи'),
        ('streak', 'Серия решений'),
        ('subject_focus', 'Фокус на предмете'),
        ('time_limit', 'На время'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    challenge_type = models.CharField(max_length=20, choices=CHALLENGE_TYPES, verbose_name="Тип вызова")
    target_value = models.IntegerField(verbose_name="Целевое значение")
    reward_xp = models.IntegerField(default=50, verbose_name="Награда (XP)")  # type: ignore
    date = models.DateField(verbose_name="Дата")
    
    class Meta:
        verbose_name = "Ежедневный вызов"
        verbose_name_plural = "Ежедневные вызовы"
        unique_together = ['challenge_type', 'date']
    
    def __str__(self):
        return f"{self.title} ({self.date})"


class UserChallenge(models.Model):
    """Прогресс пользователя по ежедневным вызовам"""
    
    profile = models.ForeignKey(UnifiedProfile, on_delete=models.CASCADE, verbose_name="Профиль")
    challenge = models.ForeignKey(DailyChallenge, on_delete=models.CASCADE, verbose_name="Вызов")
    current_progress = models.IntegerField(default=0, verbose_name="Текущий прогресс")  # type: ignore
    is_completed = models.BooleanField(default=False, verbose_name="Завершен")  # type: ignore
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Дата завершения")
    
    class Meta:
        verbose_name = "Прогресс по вызову"
        verbose_name_plural = "Прогресс по вызовам"
        unique_together = ['profile', 'challenge']
    
    def __str__(self):
        return f"{self.profile.display_name} - {self.challenge.title}"  # type: ignore
    
    @property
    def progress_percentage(self):
        """Процент выполнения"""
        if self.challenge.target_value == 0:  # type: ignore
            return 0
        return min(100, (self.current_progress / self.challenge.target_value) * 100)  # type: ignore
