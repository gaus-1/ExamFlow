from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


@csrf_exempt
@require_http_methods(["POST"])
def switch_theme(request):
    """
    API для переключения дизайна пользователя
    
    Принимает POST запрос с JSON:
    {
        "theme": "school" или "adult"
    }
    
    Возвращает:
    {
        "success": true/false,
        "theme": "school" или "adult",
        "message": "Описание результата"
    }
    """
    try:
        # Парсим JSON из запроса
        data = json.loads(request.body)
        theme = data.get('theme')
        
        # Проверяем валидность темы
        valid_themes = ['school', 'adult']
        if theme not in valid_themes:
            return JsonResponse({
                'success': False,
                'message': f'Неверная тема. Допустимые значения: {", ".join(valid_themes)}'
            }, status=400)
        
        # Если пользователь авторизован, сохраняем выбор в профиле
        if request.user.is_authenticated:
            try:
                # Создаем или обновляем предпочтение пользователя
                from .models import UserThemePreference
                preference, created = UserThemePreference.objects.get_or_create(  # type: ignore
                    user=request.user,
                    defaults={'theme': theme}
                )
                if not created:
                    preference.theme = theme
                    preference.save()
                
                # Создаем запись об использовании темы
                from .models import ThemeUsage
                ThemeUsage.objects.create(  # type: ignore
                    user=request.user,
                    theme=theme,
                    session_duration=0,
                    page_views=1
                )
                
                print(f"Пользователь {request.user.username} переключился на тему: {theme}")
            except Exception as e:
                print(f"Ошибка сохранения темы в профиль: {e}")
        
        # Возвращаем успешный ответ
        return JsonResponse({
            'success': True,
            'theme': theme,
            'message': f'Дизайн успешно переключен на "{theme}"'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'message': 'Неверный формат JSON'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def get_current_theme(request):
    """
    API для получения текущей темы пользователя
    
    Возвращает:
    {
        "success": true,
        "theme": "school" или "adult",
        "user_authenticated": true/false
    }
    """
    try:
        # По умолчанию тема "school"
        theme = 'school'
        
        # Если пользователь авторизован, можно получить из профиля
        if request.user.is_authenticated:
            try:
                # Получаем тему из профиля пользователя
                from .models import UserThemePreference
                try:
                    preference = UserThemePreference.objects.get(user=request.user)  # type: ignore
                    theme = preference.theme
                except UserThemePreference.DoesNotExist:  # type: ignore
                    # Если предпочтения нет, создаем с дефолтной темой
                    preference = UserThemePreference.objects.create(  # type: ignore
                        user=request.user,
                        theme='school'
                    )
                    theme = preference.theme
            except Exception as e:
                print(f"Ошибка получения темы из профиля: {e}")
                theme = 'school'
        
        return JsonResponse({
            'success': True,
            'theme': theme,
            'user_authenticated': request.user.is_authenticated
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


@require_http_methods(["GET"])
def preview_theme(request, theme):
    """
    API для предварительного просмотра темы
    
    Принимает theme в URL: /themes/api/preview/school/ или /themes/api/preview/adult/
    
    Возвращает:
    {
        "success": true,
        "theme": "school" или "adult",
        "preview_data": {
            "colors": {...},
            "fonts": {...}
        }
    }
    """
    try:
        # Проверяем валидность темы
        valid_themes = ['school', 'adult']
        if theme not in valid_themes:
            return JsonResponse({
                'success': False,
                'message': f'Неверная тема. Допустимые значения: {", ".join(valid_themes)}'
            }, status=400)
        
        # Данные для предварительного просмотра
        preview_data = {
            'school': {
                'colors': {
                    'primary': '#22C55E',
                    'secondary': '#3B82F6',
                    'accent': '#8B5CF6',
                    'background': '#F8FAFC'
                },
                'fonts': {
                    'heading': 'Inter, sans-serif',
                    'body': 'Inter, sans-serif'
                },
                'style': 'Яркий и энергичный дизайн для школьников'
            },
            'adult': {
                'colors': {
                    'primary': '#1E40AF',
                    'secondary': '#475569',
                    'accent': '#0891B2',
                    'background': '#F8FAFC'
                },
                'fonts': {
                    'heading': 'Inter, sans-serif',
                    'body': 'Inter, sans-serif'
                },
                'style': 'Сдержанный профессиональный дизайн для взрослых'
            }
        }
        
        return JsonResponse({
            'success': True,
            'theme': theme,
            'preview_data': preview_data.get(theme, {})
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


def test_themes(request):
    """
    Тестовая страница для проверки переключателя дизайнов
    
    Показывает демонстрацию всех элементов дизайна
    и позволяет протестировать переключение между темами
    """
    return render(request, 'themes/test_themes.html')
