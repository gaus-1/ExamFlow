from django.contrib import admin
from .models import AiRequest, AiLimit, AiProvider, AiPromptTemplate, AiResponse


@admin.register(AiRequest)
class AiRequestAdmin(admin.ModelAdmin):
    """Административная панель для запросов к ИИ"""
    list_display = ['user', 'request_type', 'tokens_used', 'cost', 'created_at', 'ip_address']
    list_filter = ['request_type', 'created_at', 'user']
    search_fields = ['prompt', 'response', 'user__username']
    readonly_fields = ['created_at', 'tokens_used', 'cost']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'session_id', 'request_type', 'prompt', 'response')
        }),
        ('Технические детали', {
            'fields': ('tokens_used', 'cost', 'ip_address', 'created_at')
        }),
    )


@admin.register(AiLimit)
class AiLimitAdmin(admin.ModelAdmin):
    """Административная панель для лимитов ИИ"""
    list_display = ['user', 'limit_type', 'current_usage', 'max_limit', 'reset_date', 'is_exceeded_display']
    list_filter = ['limit_type', 'created_at']
    search_fields = ['user__username', 'session_id']
    readonly_fields = ['created_at', 'updated_at']
    
    def is_exceeded_display(self, obj):
        """Отображение статуса превышения лимита"""
        if obj.is_exceeded():
            return '❌ Превышен'
        return '✅ В норме'
    is_exceeded_display.short_description = 'Статус лимита'
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'session_id', 'limit_type', 'max_limit')
        }),
        ('Использование', {
            'fields': ('current_usage', 'reset_date')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AiProvider)
class AiProviderAdmin(admin.ModelAdmin):
    """Административная панель для провайдеров ИИ"""
    list_display = ['name', 'provider_type', 'is_active', 'priority', 'daily_usage', 'daily_limit', 'success_rate']
    list_filter = ['provider_type', 'is_active', 'priority']
    search_fields = ['name', 'api_url']
    readonly_fields = ['created_at', 'updated_at', 'last_used', 'response_time_avg', 'success_rate']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'provider_type', 'is_active', 'priority')
        }),
        ('API настройки', {
            'fields': ('api_key', 'api_url', 'max_tokens_per_request')
        }),
        ('Лимиты и стоимость', {
            'fields': ('daily_limit', 'daily_usage', 'cost_per_token')
        }),
        ('Статистика', {
            'fields': ('response_time_avg', 'success_rate', 'last_used')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AiPromptTemplate)
class AiPromptTemplateAdmin(admin.ModelAdmin):
    """Административная панель для шаблонов промптов"""
    list_display = ['name', 'template_type', 'is_active', 'priority', 'created_at']
    list_filter = ['template_type', 'is_active', 'priority']
    search_fields = ['name', 'prompt_template']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('name', 'template_type', 'is_active', 'priority')
        }),
        ('Шаблон', {
            'fields': ('prompt_template', 'variables')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(AiResponse)
class AiResponseAdmin(admin.ModelAdmin):
    """Административная панель для кэшированных ответов ИИ"""
    list_display = ['id', 'provider', 'tokens_used', 'usage_count', 'created_at', 'last_used']
    list_filter = ['provider', 'created_at']
    search_fields = ['prompt', 'response']
    readonly_fields = ['prompt_hash', 'created_at', 'last_used', 'usage_count']
    
    fieldsets = (
        ('Основная информация', {
            'fields': ('prompt_hash', 'provider')
        }),
        ('Содержание', {
            'fields': ('prompt', 'response')
        }),
        ('Статистика', {
            'fields': ('tokens_used', 'usage_count', 'created_at', 'last_used')
        }),
    )


# Настройки административной панели
admin.site.site_header = 'ExamFlow - Администрирование'
admin.site.site_title = 'ExamFlow Admin'
admin.site.index_title = 'Панель управления ExamFlow'
