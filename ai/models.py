# type: ignore
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class AiRequest(models.Model):
    """Модель для отслеживания запросов к ИИ"""

    REQUEST_TYPES = [
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    request_type = models.CharField(max_length=50, choices=REQUEST_TYPES)
    prompt = models.TextField()
    response = models.TextField()
    tokens_used = models.IntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=6, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = 'Запрос к ИИ'
        verbose_name_plural = 'Запросы к ИИ'
        ordering = ['-created_at']

    def __str__(self):
        user_info = self.user.username if self.user else f'Гость ({self.session_id})'  # type: ignore
        return f'{user_info} - {self.get_request_type_display()} ({self.created_at.strftime("%d.%m.%Y %H:%M")})'  # type: ignore

class AiLimit(models.Model):
    """Модель для управления лимитами ИИ"""

    LIMIT_TYPES = [
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    session_id = models.CharField(max_length=100, null=True, blank=True)
    limit_type = models.CharField(max_length=20, choices=LIMIT_TYPES)
    current_usage = models.IntegerField(default=0)
    max_limit = models.IntegerField()
    reset_date = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Лимит ИИ'
        verbose_name_plural = 'Лимиты ИИ'
        unique_together = ['user', 'session_id', 'limit_type']

    def __str__(self):
        user_info = self.user.username if self.user else f'Гость ({self.session_id})'  # type: ignore
        return f'{user_info} - {self.get_limit_type_display()}: {self.current_usage}/{self.max_limit}'  # type: ignore

    def is_exceeded(self):
        """Проверяет, превышен ли лимит"""
        return self.current_usage >= self.max_limit

    def can_make_request(self):
        """Проверяет, можно ли сделать запрос"""
        if self.is_exceeded():
            return False

        # Проверяем, не истек ли период сброса
        if timezone.now() > self.reset_date:
            self.reset_usage()
            return True

        return True

    def reset_usage(self):
        """Сбрасывает счетчик использования"""
        self.current_usage = 0
        self.reset_date = self.calculate_next_reset_date()
        self.save()

    def calculate_next_reset_date(self):
        """Вычисляет следующую дату сброса"""
        now = timezone.now()
        if self.limit_type == 'daily':
            return now + timedelta(days=1)
        elif self.limit_type == 'monthly':
            return now + timedelta(days=30)
        else:  # total
            return now + timedelta(days=365)  # Год

class AiProvider(models.Model):
    """Модель для управления провайдерами ИИ"""

    PROVIDER_TYPES = [
    ]

    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    api_key = models.CharField(max_length=500, blank=True)
    api_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)  # Приоритет использования
    daily_limit = models.IntegerField(default=1000)
    daily_usage = models.IntegerField(default=0)
    cost_per_token = models.DecimalField(max_digits=10, decimal_places=8, default=0)
    max_tokens_per_request = models.IntegerField(default=4000)
    response_time_avg = models.FloatField(default=0)  # Среднее время ответа в секундах
    success_rate = models.FloatField(default=100)  # Процент успешных запросов
    last_used = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Провайдер ИИ'
        verbose_name_plural = 'Провайдеры ИИ'
        ordering = ['priority', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_provider_type_display()})'  # type: ignore

    def can_handle_request(self):
        """Проверяет, может ли провайдер обработать запрос"""
        if not self.is_active:
            return False

        if self.daily_usage >= self.daily_limit:
            return False

        return True

    def update_usage(self, tokens_used):
        """Обновляет статистику использования"""
        self.daily_usage += 1  # type: ignore
        self.last_used = timezone.now()
        self.save()

class AiPromptTemplate(models.Model):
    """Модель для шаблонов промптов"""

    TEMPLATE_TYPES = [
    ]

    name = models.CharField(max_length=200)
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    prompt_template = models.TextField()
    variables = models.JSONField(default=dict,
                                 help_text='Переменные для подстановки в шаблон')
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Шаблон промпта'
        verbose_name_plural = 'Шаблоны промптов'
        ordering = ['priority', 'name']

    def __str__(self):
        return f'{self.name} ({self.get_template_type_display()})'  # type: ignore

    def format_prompt(self, **kwargs):
        """Форматирует промпт с подстановкой переменных"""
        try:
            return self.prompt_template.format(**kwargs)  # type: ignore
        except KeyError:
            # Если не хватает переменных, возвращаем исходный шаблон
            return self.prompt_template

class AiResponse(models.Model):
    """Модель для кэширования ответов ИИ"""

    prompt_hash = models.CharField(max_length=64, unique=True)
    prompt = models.TextField()
    response = models.TextField()
    tokens_used = models.IntegerField(default=0)
    provider = models.ForeignKey(AiProvider, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    usage_count = models.IntegerField(default=1)

    class Meta:
        verbose_name = 'Ответ ИИ'
        verbose_name_plural = 'Ответы ИИ'
        ordering = ['-last_used']

    def __str__(self):
        return f'Ответ {self.id} ({self.created_at.strftime("%d.%m.%Y %H:%M")})'  # type: ignore

    def increment_usage(self):
        """Увеличивает счетчик использования"""
        self.usage_count += 1  # type: ignore
        self.last_used = timezone.now()
        self.save()
