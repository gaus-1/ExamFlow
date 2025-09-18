#!/usr/bin/env python3
"""
Демонстрация работы модуля управления дизайнами (themes)

Этот файл содержит примеры использования модуля themes
для разработчиков и тестирования.
"""

from .models import UserThemePreference, ThemeUsage, ThemeCustomization
import os
import django

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')
django.setup()

def demo_theme_management():
    """Демонстрация управления темами"""
    print("🎨 ДЕМОНСТРАЦИЯ МОДУЛЯ УПРАВЛЕНИЯ ДИЗАЙНАМИ")
    print("=" * 60)

    # Создаем тестового пользователя
    user, created = User.objects.get_or_create( # type: ignore
        username='demo_user',
        defaults={
            'email': 'demo@examflow.ru',
            'first_name': 'Демо',
            'last_name': 'Пользователь'
        }
    )

    if created:
        user.set_password('demo123')
        user.save()
        print("✅ Создан тестовый пользователь: {user.username}")
    else:
        print("📝 Используется существующий пользователь: {user.username}")

    print()

    # Демонстрация работы с предпочтениями тем
    print("1️⃣ УПРАВЛЕНИЕ ПРЕДПОЧТЕНИЯМИ ТЕМ")
    print("-" * 40)

    # Создаем предпочтение темы
    preference, created = UserThemePreference.objects.get_or_create( # type: ignore
        user=user,
        defaults={'theme': 'school'}
    )

    if created:
        print("✅ Создано предпочтение темы: {preference.get_theme_display()}")
    else:
        print("📝 Текущее предпочтение: {preference.get_theme_display()}")

    # Переключаем тему
    old_theme = preference.theme
    new_theme = 'adult' if old_theme == 'school' else 'school'
    preference.theme = new_theme
    preference.save()

    print("🔄 Тема изменена: {preference.get_theme_display()}")
    print("   Старая тема: {dict(UserThemePreference.THEME_CHOICES)[old_theme]}")
    print("   Новая тема: {dict(UserThemePreference.THEME_CHOICES)[new_theme]}")

    print()

    # Демонстрация отслеживания использования
    print("2️⃣ ОТСЛЕЖИВАНИЕ ИСПОЛЬЗОВАНИЯ ТЕМ")
    print("-" * 40)

    # Создаем записи об использовании
    usage_data = [
    ]

    for data in usage_data:
        usage = ThemeUsage.objects.create( # type: ignore
            user=user,
            **data
        )
        print("✅ Создана запись использования: {usage.get_theme_display()}")
        print("   Время сессии: {usage.get_session_duration_minutes()} мин")
        print("   Просмотрено страниц: {usage.page_views}")

    print()

    # Демонстрация пользовательских настроек
    print("3️⃣ ПОЛЬЗОВАТЕЛЬСКИЕ НАСТРОЙКИ ТЕМ")
    print("-" * 40)

    # Создаем кастомные настройки
    custom_colors = {
        'primary': '#FF6B6B',
        'secondary': '#4ECDC4',
        'accent': '#45B7D1'
    }

    custom_fonts = {
        'main': 'Roboto',
        'heading': 'Montserrat',
        'mono': 'JetBrains Mono'
    }

    customization, created = ThemeCustomization.objects.get_or_create( # type: ignore
        user=user,
        theme='school',
        defaults={
            'custom_colors': custom_colors,
            'custom_fonts': custom_fonts,
            'is_active': True
        }
    )

    if created:
        print(
            "✅ Созданы пользовательские настройки для темы: {customization.get_theme_display()}")
    else:
        print(
            "📝 Обновлены пользовательские настройки для темы: {customization.get_theme_display()}")

    print("   Кастомные цвета: {len(customization.custom_colors)} цветов")
    print("   Кастомные шрифты: {len(customization.custom_fonts)} шрифтов")

    print()

    # Статистика по темам
    print("4️⃣ СТАТИСТИКА ИСПОЛЬЗОВАНИЯ ТЕМ")
    print("-" * 40)

    total_usage = ThemeUsage.objects.filter(user=user) # type: ignore
    school_usage = total_usage.filter(theme='school')
    adult_usage = total_usage.filter(theme='adult')

    print("📊 Общая статистика для пользователя {user.username}:")
    print("   Всего записей: {total_usage.count()}")
    print("   Использование школьной темы: {school_usage.count()} раз")
    print("   Использование взрослой темы: {adult_usage.count()} раз")

    # Время использования по темам
    school_time = sum(usage.session_duration for usage in school_usage)
    adult_time = sum(usage.session_duration for usage in adult_usage)

    print("   Время в школьной теме: {school_time // 60} мин")
    print("   Время во взрослой теме: {adult_time // 60} мин")

    # Страницы по темам
    school_pages = sum(usage.page_views for usage in school_usage)
    adult_pages = sum(usage.page_views for usage in adult_usage)

    print("   Страниц в школьной теме: {school_pages}")
    print("   Страниц во взрослой теме: {adult_pages}")

    print()

    # Демонстрация методов моделей
    print("5️⃣ ДЕМОНСТРАЦИЯ МЕТОДОВ МОДЕЛЕЙ")
    print("-" * 40)

    # Методы UserThemePreference
    print("🎯 Методы UserThemePreference:")
    print("   Текущая тема: {preference.get_theme_display()}")
    print("   Можно переключить: {preference.can_switch_theme()}")

    # Методы ThemeUsage
    latest_usage = ThemeUsage.objects.filter(user=user).latest('created_at') # type: ignore
    print("📈 Методы ThemeUsage:")
    print("   Последнее использование: {latest_usage.get_theme_display()}")
    print("   Время сессии: {latest_usage.get_session_duration_minutes()} мин")

    # Методы ThemeCustomization
    if customization.is_active:
        print("🎨 Методы ThemeCustomization:")
        print("   Есть кастомизация: {customization.has_customizations()}")
        print(
            "   Основной цвет: {customization.get_custom_color('primary', '#000000')}")
        print("   Основной шрифт: {customization.get_custom_font('main', 'Arial')}")

    print()
    print("🎉 Демонстрация завершена!")
    print("=" * 60)

def demo_api_endpoints():
    """Демонстрация API endpoints"""
    print("🌐 ДЕМОНСТРАЦИЯ API ENDPOINTS")
    print("=" * 60)

    print("Доступные API endpoints:")
    print("  GET  /themes/test/                    - Тестовая страница")
    print("  POST /themes/api/switch/              - Переключение темы")
    print("  GET  /themes/api/current/             - Текущая тема")
    print("  GET  /themes/api/preview/<theme>/     - Предварительный просмотр")

    print()
    print("Примеры использования:")
    print("  # Переключение на взрослую тему")
    print("  curl -X POST /themes/api/switch/ \\")
    print("       -H 'Content-Type: application/json' \\")
    print("       -d '{\"theme\": \"adult\"}'")

    print()
    print("  # Получение текущей темы")
    print("  curl /themes/api/current/")

    print()
    print("  # Предварительный просмотр школьной темы")
    print("  curl /themes/api/preview/school/")

    print()
    print("=" * 60)

if __name__ == '__main__':
    try:
        demo_theme_management()
        print()
        demo_api_endpoints()
    except Exception as e:
        print("❌ Ошибка при выполнении демонстрации: {e}")
        import traceback
        traceback.print_exc()
