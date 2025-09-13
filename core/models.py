"""
Модели для приложения core
"""

from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class Subject(models.Model):
    """Модель предмета"""
    name = models.CharField(max_length=100, verbose_name="Название")
    code = models.CharField(max_length=10, unique=True, verbose_name="Код предмета")
    exam_type = models.CharField(max_length=20, choices=[
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
        return "{self.name} ({self.get_exam_type_display()})"  # type: ignore

    @property
    def task_count(self):
        """Количество задач по предмету"""
        return self.task_set.count()  # type: ignore

class Task(models.Model):
    """Модель задачи"""
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        verbose_name="Предмет")
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
        return "{self.subject.name}: {self.title}"

    def check_answer(self, user_answer):
        """Проверяет правильность ответа пользователя"""
        if not self.answer:
            return False
        return str(user_answer).strip().lower() == str(self.answer).strip().lower()

class UserProgress(models.Model):
    """Модель прогресса пользователя по задаче"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь",
        related_name='core_userprogress_set')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, verbose_name="Задача")
    user_answer = models.CharField(
        max_length=200,
        blank=True,
        verbose_name="Ответ пользователя")
    is_correct = models.BooleanField(default=False,  # type: ignore
                                     verbose_name="Правильно решено")  # type: ignore
    attempts = models.IntegerField(
        default=1, verbose_name="Количество попыток")  # type: ignore
    time_spent = models.IntegerField(
        default=0, verbose_name="Время в секундах")  # type: ignore
    last_attempt = models.DateTimeField(auto_now=True, verbose_name="Последняя попытка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Прогресс пользователя"
        verbose_name_plural = "Прогресс пользователей"
        unique_together = ['user', 'task']
        ordering = ['-last_attempt']

    def __str__(self):
        return "{self.user.username} - {self.task.title}"  # type: ignore

class UnifiedProfile(models.Model):
    """Унифицированный профиль пользователя для сайта и бота"""

    # Основная информация
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь Django",
        null=True,
        blank=True)
    telegram_id = models.BigIntegerField(unique=True, verbose_name="Telegram ID")
    telegram_username = models.CharField(
        max_length=100, blank=True, verbose_name="Telegram Username")

    # Профиль пользователя
    display_name = models.CharField(max_length=100, verbose_name="Отображаемое имя")
    avatar_url = models.URLField(blank=True, verbose_name="URL аватара")

    # Настройки
    preferred_subjects = models.ManyToManyField(
        Subject, blank=True, verbose_name="Предпочитаемые предметы")
    notification_settings = models.JSONField(
        default=dict, verbose_name="Настройки уведомлений")

    # Статистика и прогресс
    total_solved = models.IntegerField(
        default=0, verbose_name="Всего решено задач")  # type: ignore
    current_streak = models.IntegerField(
        default=0, verbose_name="Текущая серия")  # type: ignore
    best_streak = models.IntegerField(
        default=0, verbose_name="Лучшая серия")  # type: ignore

    # Gamification
    level = models.IntegerField(default=1, verbose_name="Уровень")  # type: ignore
    experience_points = models.IntegerField(
        default=0, verbose_name="Очки опыта")  # type: ignore
    achievements = models.JSONField(default=list, verbose_name="Достижения")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")
    last_activity = models.DateTimeField(
        auto_now=True, verbose_name="Последняя активность")

    class Meta:
        verbose_name = "Унифицированный профиль"
        verbose_name_plural = "Унифицированные профили"
        ordering = ['-last_activity']

    def __str__(self):
        return "{self.display_name} (TG: {self.telegram_id})"

    @property
    def experience_to_next_level(self):
        """Опыт, необходимый для следующего уровня"""
        return (self.level * 100) - (self.experience_points %  # type: ignore

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
    ]

    title = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание")
    challenge_type = models.CharField(
        max_length=20,
        choices=CHALLENGE_TYPES,
        verbose_name="Тип вызова")
    target_value = models.IntegerField(verbose_name="Целевое значение")
    reward_xp = models.IntegerField(default=50,  # type: ignore
                                    verbose_name="Награда (XP)")  # type: ignore
    date = models.DateField(verbose_name="Дата")

    class Meta:
        verbose_name = "Ежедневный вызов"
        verbose_name_plural = "Ежедневные вызовы"
        unique_together = ['challenge_type', 'date']

    def __str__(self):
        return "{self.title} ({self.date})"

class UserChallenge(models.Model):
    """Прогресс пользователя по ежедневным вызовам"""

    profile = models.ForeignKey(
        UnifiedProfile,
        on_delete=models.CASCADE,
        verbose_name="Профиль")
    challenge = models.ForeignKey(
        DailyChallenge,
        on_delete=models.CASCADE,
        verbose_name="Вызов")
    current_progress = models.IntegerField(
        default=0, verbose_name="Текущий прогресс")  # type: ignore
    is_completed = models.BooleanField(
        default=False, verbose_name="Завершен")  # type: ignore
    completed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата завершения")

    class Meta:
        verbose_name = "Прогресс по вызову"
        verbose_name_plural = "Прогресс по вызовам"
        unique_together = ['profile', 'challenge']

    def __str__(self):
        return "{self.profile.display_name} - {self.challenge.title}"  # type: ignore

    @property
    def progress_percentage(self):
        """Процент выполнения"""
        if self.challenge.target_value == 0:  # type: ignore
            return 0
        return min(
            100,
             self.challenge.target_value) *  # type: ignore
            100)  # type: ignore

class ChatSession(models.Model):
    """Сессия чата пользователя с ботом для сохранения контекста"""
    user = models.ForeignKey(
        'auth.User',  # type: ignore
        on_delete=models.CASCADE,
        verbose_name="Пользователь")  # type: ignore
    telegram_id = models.BigIntegerField(verbose_name="Telegram ID")
    session_id = models.CharField(max_length=100, unique=True, verbose_name="ID сессии")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Создана")
    last_activity = models.DateTimeField(
        auto_now=True, verbose_name="Последняя активность")
    context_messages = models.JSONField(default=list, verbose_name="История сообщений")
    max_context_length = models.IntegerField(
        default=10, verbose_name="Максимальная длина контекста")  # type: ignore

    class Meta:
        verbose_name = "Сессия чата"
        verbose_name_plural = "Сессии чата"
        indexes = [
            models.Index(fields=['telegram_id', 'session_id']),
            models.Index(fields=['last_activity']),
        ]

    def __str__(self):
        return "Сессия {self.session_id} для {self.user.username}"  # type: ignore

    def add_message(self, role: str, content: str):
        """Добавляет сообщение в контекст сессии"""
        message = {
            'role': role,  # 'user' или 'assistant'
            'content': content,
            'timestamp': timezone.now().isoformat()
        }
        self.context_messages.append(message)  # type: ignore

        # Ограничиваем длину контекста
        if len(self.context_messages) > self.max_context_length:  # type: ignore
            # Оставляем первые 2 сообщения (системные) и последние max_context_length-2
            self.context_messages = (
                self.context_messages[:2] +  # type: ignore
                self.context_messages[-(self.max_context_length - 2):]  # type: ignore
            )

        self.save()

    def get_context_for_ai(self) -> str:
        """Возвращает контекст в формате для ИИ"""
        if not self.context_messages:
            return ""

        context_parts = []
        for msg in self.context_messages[-self.max_context_length:]:  # type: ignore
            # type: ignore
            role = "Пользователь" if msg['role'] == 'user' else "Ассистент"
            context_parts.append("{role}: {msg['content']}")  # type: ignore

        return "\n".join(context_parts)

    def clear_context(self):
        """Очищает контекст сессии"""
        self.context_messages = []  # type: ignore
        self.save()

class FIPIData(models.Model):
    """Модель для хранения данных с ФИПИ"""

    DATA_TYPES = [
    ]

    title = models.CharField(max_length=500, verbose_name="Название")
    url = models.URLField(verbose_name="URL")
    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPES,
        verbose_name="Тип данных")
    subject = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Предмет")
    exam_type = models.CharField(max_length=20, choices=[
    ], default='ege', verbose_name="Тип экзамена")
    content_hash = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Хеш содержимого")
    content = models.TextField(blank=True, verbose_name="Содержимое")
    collected_at = models.DateTimeField(verbose_name="Дата сбора")
    processed_at = models.DateTimeField(
        null=True, blank=True, verbose_name="Дата обработки")
    is_processed = models.BooleanField(
        default=False, verbose_name="Обработано")  # type: ignore
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Данные ФИПИ"
        verbose_name_plural = "Данные ФИПИ"
        ordering = ['-collected_at']
        indexes = [
            models.Index(fields=['data_type']),
            models.Index(fields=['subject']),
            models.Index(fields=['is_processed']),
            models.Index(fields=['collected_at']),
        ]

    def __str__(self):
        return "{self.title} ({self.get_data_type_display()})"  # type: ignore

    def mark_as_processed(self):
        """Отмечает запись как обработанную"""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save()

class DataChunk(models.Model):
    """Модель для хранения чанков текста с векторными представлениями"""

    source_data = models.ForeignKey(
        FIPIData,
        on_delete=models.CASCADE,
        verbose_name="Исходные данные")  # type: ignore
    chunk_text = models.TextField(verbose_name="Текст чанка")
    chunk_index = models.IntegerField(verbose_name="Индекс чанка")
    embedding = models.JSONField(verbose_name="Векторное представление (JSON)")
    # pgvector поле для быстрого поиска
    embedding_vector = models.TextField(
        blank=True,
        null=True,
        help_text='Vector embedding for semantic search (pgvector)')
    subject = models.CharField(max_length=50, blank=True, verbose_name="Предмет")
    document_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Тип документа")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="Метаданные")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Чанк данных"
        verbose_name_plural = "Чанки данных"
        ordering = ['source_data', 'chunk_index']
        unique_together = ['source_data', 'chunk_index']
        indexes = [
            models.Index(fields=['source_data']),
            models.Index(fields=['chunk_index']),
        ]

    def __str__(self):
        # type: ignore
        return "Чанк {self.chunk_index} из {self.source_data.title[:50]}..."

class UserProfile(models.Model):
    """Модель профиля пользователя для персонализации"""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        verbose_name="Пользователь")  # type: ignore
    query_stats = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Статистика запросов")
    recent_queries = models.JSONField(
        default=list,
        blank=True,
        verbose_name="Последние запросы")
    preferred_subjects = models.JSONField(
        default=list, blank=True, verbose_name="Предпочитаемые предметы")
    difficulty_preference = models.CharField(
        max_length=20,
        choices=[
        ],
        default='medium',
        verbose_name="Предпочитаемая сложность")
    subscription_type = models.CharField(
        max_length=20,
        choices=[
        ],
        default='free',
        verbose_name="Тип подписки")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"

    def __str__(self):
        return "Профиль {self.user.username}"  # type: ignore

    @property
    def total_queries(self):
        """Общее количество запросов"""
        return sum(self.query_stats.values()) if self.query_stats else 0  # type: ignore

    @property
    def is_premium(self):
        """Проверяет, является ли пользователь премиум"""
        return self.subscription_type == 'premium'

class FIPISourceMap(models.Model):
    """Модель для хранения карты источников данных fipi.ru"""

    DATA_TYPES = [
    ]

    EXAM_TYPES = [
    ]

    PRIORITIES = [
    ]

    UPDATE_FREQUENCIES = [
    ]

    FILE_FORMATS = [
    ]

    # Основные поля
    source_id = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ID источника")
    name = models.CharField(max_length=500, verbose_name="Название")
    url = models.URLField(verbose_name="URL")
    data_type = models.CharField(
        max_length=50,
        choices=DATA_TYPES,
        verbose_name="Тип данных")
    exam_type = models.CharField(
        max_length=20,
        choices=EXAM_TYPES,
        verbose_name="Тип экзамена")
    subject = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name="Предмет")

    # Приоритет и частота обновления
    priority = models.IntegerField(
        choices=PRIORITIES,
        default=3,  # type: ignore
        verbose_name="Приоритет")  # type: ignore
    update_frequency = models.CharField(
        max_length=20,
        choices=UPDATE_FREQUENCIES,
        default='annually',
        verbose_name="Частота обновления")

    # Технические характеристики
    file_format = models.CharField(
        max_length=10,
        choices=FILE_FORMATS,
        default='HTML',
        verbose_name="Формат файла")
    description = models.TextField(blank=True, verbose_name="Описание")

    # Статус и мониторинг
    is_active = models.BooleanField(
        default=True, verbose_name="Активен")  # type: ignore
    last_checked = models.DateTimeField(
        null=True, blank=True, verbose_name="Последняя проверка")
    content_hash = models.CharField(
        max_length=64,
        blank=True,
        null=True,
        verbose_name="Хеш содержимого")
    last_updated = models.DateTimeField(
        null=True, blank=True, verbose_name="Последнее обновление")

    # Временные метки
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Дата обновления")

    class Meta:
        verbose_name = "Источник данных ФИПИ"
        verbose_name_plural = "Источники данных ФИПИ"
        ordering = ['priority', 'data_type', 'subject']
        indexes = [
            models.Index(fields=['priority']),
            models.Index(fields=['data_type']),
            models.Index(fields=['exam_type']),
            models.Index(fields=['subject']),
            models.Index(fields=['is_active']),
            models.Index(fields=['last_checked']),
        ]

    def __str__(self):
        return "{self.name} ({self.get_data_type_display()})"  # type: ignore

    @property
    def is_critical(self) -> bool:
        """Проверяет, является ли источник критически важным"""
        return self.priority == 1

    @property
    def is_high_priority(self) -> bool:
        """Проверяет, является ли источник высокоприоритетным"""
        return self.priority <= 2

    def mark_as_checked(self, content_hash: str = None):  # type: ignore
        """Отмечает источник как проверенный"""
        from django.utils import timezone
        self.last_checked = timezone.now()
        if content_hash:
            self.content_hash = content_hash
        self.save()

    def mark_as_updated(self):
        """Отмечает источник как обновленный"""
        from django.utils import timezone
        self.last_updated = timezone.now()
        self.save()

    def needs_update(self) -> bool:
        """Проверяет, нуждается ли источник в обновлении"""
        if not self.last_checked:
            return True

        from django.utils import timezone
        now = timezone.now()
        last_checked = self.last_checked  # type: ignore
        if self.update_frequency == 'daily':
            return (now - last_checked).days >= 1  # type: ignore
        elif self.update_frequency == 'weekly':
            return (now - last_checked).days >= 7  # type: ignore
        elif self.update_frequency == 'monthly':
            return (now - last_checked).days >= 30  # type: ignore
        elif self.update_frequency == 'annually':
            return (now - last_checked).days >= 365  # type: ignore

        return False
