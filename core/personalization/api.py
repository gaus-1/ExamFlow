"""
API для системы персонализации ExamFlow 2.0
"""

import json
import logging
from django.http import JsonResponse
from django.db import models
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.views import View
from django.utils.decorators import method_decorator

from core.personalization.recommendation_engine import RecommendationEngine

logger = logging.getLogger(__name__)


class PersonalizationAPI(View):
    """
    API для персонализации и рекомендаций
    """

    def __init__(self):
        self.recommendation_engine = RecommendationEngine()

    def get(self, request):
        """
        GET запрос для получения персонализированных рекомендаций
        """
        try:
            user_id = request.user.id if request.user.is_authenticated else None

            if not user_id:
                return JsonResponse({
                    'error': 'Пользователь не авторизован'
                }, status=401)

            # Получаем параметры
            limit = int(request.GET.get('limit', 5))

            # Получаем рекомендации
            recommendations = self.recommendation_engine.get_personalized_recommendations(
                user_id, limit)

            return JsonResponse({
                'status': 'success',
                'recommendations': recommendations,
                'generated_at': self.get_current_timestamp()
            })

        except Exception as e:
            logger.error(f"Ошибка PersonalizationAPI: {e}")
            return JsonResponse({
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, status=500)

    def post(self, request):
        """
        POST запрос для обновления предпочтений пользователя
        """
        try:
            user_id = request.user.id if request.user.is_authenticated else None

            if not user_id:
                return JsonResponse({
                    'error': 'Пользователь не авторизован'
                }, status=401)

            data = json.loads(request.body)
            action = data.get('action')

            if action == 'update_preferences':
                return self.update_user_preferences(user_id, data)
            elif action == 'mark_topic_completed':
                return self.mark_topic_completed(user_id, data)
            elif action == 'update_learning_style':
                return self.update_learning_style(user_id, data)
            else:
                return JsonResponse({
                    'error': 'Неизвестное действие'
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"Ошибка PersonalizationAPI POST: {e}")
            return JsonResponse({
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, status=500)

    def update_user_preferences(self, user_id: int, data: dict) -> JsonResponse:
        """
        Обновляет предпочтения пользователя
        """
        try:
            from core.models import UnifiedProfile  # type: ignore

            # Получаем профиль пользователя
            user_profile = UnifiedProfile.objects.filter(  # type: ignore
                models.Q(
                    user_id=user_id) | models.Q(
                    telegram_id=user_id)  # type: ignore
            ).first()

            if not user_profile:
                return JsonResponse({
                    'error': 'Профиль пользователя не найден'
                }, status=404)

            # Обновляем предпочтения
            preferred_subjects = data.get('preferred_subjects', [])
            if preferred_subjects:
                # Здесь можно обновить предпочтения по предметам
                pass

            learning_style = data.get('learning_style')
            if learning_style:
                # Обновляем стиль обучения
                user_profile.learning_style = learning_style
                user_profile.save()

            return JsonResponse({
                'status': 'success',
                'message': 'Предпочтения обновлены'
            })

        except Exception as e:
            logger.error(f"Ошибка при обновлении предпочтений: {e}")
            return JsonResponse({
                'error': f'Ошибка обновления: {str(e)}'
            }, status=500)

    def mark_topic_completed(self, user_id: int, data: dict) -> JsonResponse:
        """
        Отмечает тему как завершенную
        """
        try:
            topic = data.get('topic')
            if not topic:
                return JsonResponse({
                    'error': 'Не указана тема'
                }, status=400)

            # Здесь можно добавить логику отметки темы как завершенной
            # Например, обновить прогресс пользователя

            return JsonResponse({
                'status': 'success',
                'message': f'Тема "{topic}" отмечена как завершенная'
            })

        except Exception as e:
            logger.error(f"Ошибка при отметке темы: {e}")
            return JsonResponse({
                'error': f'Ошибка отметки: {str(e)}'
            }, status=500)

    def update_learning_style(self, user_id: int, data: dict) -> JsonResponse:
        """
        Обновляет стиль обучения пользователя
        """
        try:
            learning_style = data.get('learning_style')
            if not learning_style:
                return JsonResponse({
                    'error': 'Не указан стиль обучения'
                }, status=400)

            valid_styles = ['visual', 'auditory', 'kinesthetic', 'reading']
            if learning_style not in valid_styles:
                return JsonResponse({
                    'error': f'Неверный стиль обучения. Доступные: {valid_styles}'
                }, status=400)

            from core.models import UnifiedProfile  # type: ignore

            user_profile = UnifiedProfile.objects.filter(  # type: ignore
                models.Q(
                    user_id=user_id) | models.Q(
                    telegram_id=user_id)  # type: ignore
            ).first()

            if user_profile:
                user_profile.learning_style = learning_style
                user_profile.save()

            return JsonResponse({
                'status': 'success',
                'message': f'Стиль обучения обновлен на {learning_style}'
            })

        except Exception as e:
            logger.error(f"Ошибка при обновлении стиля обучения: {e}")
            return JsonResponse({
                'error': f'Ошибка обновления: {str(e)}'
            }, status=500)

    def get_current_timestamp(self) -> str:
        """
        Возвращает текущую временную метку
        """
        from django.utils import timezone
        return timezone.now().isoformat()


@method_decorator(login_required, name='dispatch')
class LearningPathAPI(View):
    """
    API для персонального пути обучения
    """

    def __init__(self):
        self.recommendation_engine = RecommendationEngine()

    def get(self, request):
        """
        GET запрос для получения персонального пути обучения
        """
        try:
            user_id = request.user.id

            # Получаем анализ пользователя
            user_analysis = self.recommendation_engine.analyze_user_progress(user_id)

            # Получаем путь обучения
            learning_path = self.recommendation_engine.get_learning_path(user_analysis)

            return JsonResponse({
                'status': 'success',
                'learning_path': learning_path,
                'user_analysis': {
                    'total_problems_solved': user_analysis.get('total_problems_solved', 0),
                    'average_accuracy': user_analysis.get('average_accuracy', 0),
                    'learning_velocity': user_analysis.get('learning_velocity', 0)
                }
            })

        except Exception as e:
            logger.error(f"Ошибка LearningPathAPI: {e}")
            return JsonResponse({
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, status=500)


# URL маршруты
@csrf_exempt
@require_http_methods(["GET", "POST"])
def personalization_api(request):
    """
    API endpoint для персонализации
    """
    view = PersonalizationAPI()
    if request.method == 'GET':
        return view.get(request)
    else:
        return view.post(request)


@require_http_methods(["GET"])
def learning_path_api(request):
    """
    API endpoint для пути обучения
    """
    view = LearningPathAPI()
    return view.get(request)
