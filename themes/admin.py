from django.contrib import admin
from .models import UserThemePreference, ThemeUsage, ThemeCustomization


@admin.register(UserThemePreference)
class UserThemePreferenceAdmin(admin.ModelAdmin):
    """
    Административная панель для управления предпочтениями пользователей по дизайну
    """

    list_display = [
        'user',
        'theme',
        'is_active',
        'created_at',
        'updated_at'
    ]

    list_filter = [
        'theme',
        'is_active',
        'created_at',
        'updated_at'
    ]

    search_fields = [
        'user__username',
        'user__email',
        'user__first_name',
        'user__last_name'
    ]

    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    list_per_page = 25

    actions = [
        'activate_themes',
        'deactivate_themes',
        'switch_to_school',
        'switch_to_adult']

    def activate_themes(self, request, queryset):
        """Активировать выбранные темы"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} тем')
    activate_themes.short_description = "Активировать выбранные темы"

    def deactivate_themes(self, request, queryset):
        """Деактивировать выбранные темы"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Деактивировано {updated} тем')
    deactivate_themes.short_description = "Деактивировать выбранные темы"

    def switch_to_school(self, request, queryset):
        """Переключить выбранные темы на школьный дизайн"""
        updated = queryset.update(theme='school')
        self.message_user(request, f'Переключено {updated} тем на школьный дизайн')
    switch_to_school.short_description = "Переключить на школьный дизайн"

    def switch_to_adult(self, request, queryset):
        """Переключить выбранные темы на взрослый дизайн"""
        updated = queryset.update(theme='adult')
        self.message_user(request, f'Переключено {updated} тем на взрослый дизайн')
    switch_to_adult.short_description = "Переключить на взрослый дизайн"

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'theme', 'is_active')
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ThemeUsage)
class ThemeUsageAdmin(admin.ModelAdmin):
    """
    Административная панель для управления статистикой использования тем
    """

    list_display = [
        'user',
        'theme',
        'session_duration',
        'page_views',
        'created_at',
        'get_session_duration_minutes_display'
    ]

    list_filter = [
        'theme',
        'created_at',
        'session_duration',
        'page_views'
    ]

    search_fields = [
        'user__username',
        'user__email'
    ]

    readonly_fields = [
        'created_at'
    ]

    list_per_page = 25

    def get_session_duration_minutes_display(self, obj):
        """Отображение продолжительности сессии в минутах"""
        return f"{obj.get_session_duration_minutes()} мин"
    get_session_duration_minutes_display.short_description = 'Длительность (мин)'

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'theme')
        }),
        ('Статистика использования', {
            'fields': ('session_duration', 'page_views')
        }),
        ('Временные метки', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(ThemeCustomization)
class ThemeCustomizationAdmin(admin.ModelAdmin):
    """
    Административная панель для управления пользовательскими настройками тем
    """

    list_display = [
        'user',
        'theme',
        'is_active',
        'has_customizations_display',
        'created_at',
        'updated_at'
    ]

    list_filter = [
        'theme',
        'is_active',
        'created_at',
        'updated_at'
    ]

    search_fields = [
        'user__username',
        'user__email'
    ]

    readonly_fields = [
        'created_at',
        'updated_at'
    ]

    list_per_page = 25

    actions = ['activate_customizations', 'deactivate_customizations']

    def has_customizations_display(self, obj):
        """Отображение наличия пользовательских настроек"""
        return "Да" if obj.has_customizations() else "Нет"
    has_customizations_display.short_description = 'Есть настройки'
    has_customizations_display.boolean = True

    def activate_customizations(self, request, queryset):
        """Активировать выбранные пользовательские настройки"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Активировано {updated} пользовательских настроек')
    activate_customizations.short_description = "Активировать настройки"

    def deactivate_customizations(self, request, queryset):
        """Деактивировать выбранные пользовательские настройки"""
        updated = queryset.update(is_active=False)
        self.message_user(
            request,
            f'Деактивировано {updated} пользовательских настроек')
    deactivate_customizations.short_description = "Деактивировать настройки"

    fieldsets = (
        ('Основная информация', {
            'fields': ('user', 'theme', 'is_active')
        }),
        ('Пользовательские настройки', {
            'fields': ('custom_colors', 'custom_fonts'),
            'description': 'JSON-формат для пользовательских цветов и шрифтов'
        }),
        ('Временные метки', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


# Настройки административной панели
admin.site.site_header = "ExamFlow - Администрирование"
admin.site.site_title = "ExamFlow Admin"
admin.site.index_title = "Панель управления ExamFlow"
