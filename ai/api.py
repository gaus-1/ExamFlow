"""
API для AI ассистента ExamFlow 2.0

Обрабатывает:
- Запросы к ИИ-ассистенту через Gemini API
- Получение задач по темам
- Проверку ответов
- Пользовательский профиль
"""

import os
from typing import Dict, List, Optional, Union, Any, Tuple
import google.generativeai as genai
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views import View
import json
import logging
import hashlib
from django.core.cache import cache

logger = logging.getLogger(__name__)

# Настройка Gemini API
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise RuntimeError('SECURITY: GEMINI_API_KEY must be set in environment variables')
# Инициализация модели с оптимизацией для скорости
try:
    genai.configure(api_key=GEMINI_API_KEY)  # type: ignore
    # Используем более быструю модель с настройками для скорости
    model = genai.GenerativeModel(
        'gemini-1.5-flash',
        generation_config=genai.types.GenerationConfig(
            max_output_tokens=1000,  # Ограничиваем длину ответа
            temperature=0.7,  # Баланс между креативностью и скоростью
            top_p=0.8,
            top_k=40
        )
    )  # type: ignore
except Exception as e:
    logger.error(f"Ошибка инициализации Gemini API: {e}")
    model = None


class AIAssistantAPI(View):
    """
    API для ИИ-ассистента с реальным Gemini API

    Обрабатывает запросы пользователей и возвращает структурированные ответы
    с предложениями практики
    """

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        Обрабатывает POST запросы к ИИ-ассистенту

        Ожидает JSON:
        {
            "prompt": "Вопрос пользователя"
        }

        Возвращает JSON:
        {
            "answer": "Ответ ИИ",
            "sources": [{"title": "Название", "url": "ссылка"}],
            "practice": {
                "topic": "тема",
                "description": "Описание практики"
            }
        }
        """
        try:
            logger.info(f"AI API: Получен запрос от {request.META.get('REMOTE_ADDR')}")

            # Валидация размера запроса
            if len(request.body) > 10000:  # 10KB лимит
                return JsonResponse({
                    'error': 'Слишком большой запрос'
                }, status=413)

            data = json.loads(request.body)
            prompt = data.get('prompt', '').strip()

            # Валидация промпта
            if not prompt:
                return JsonResponse({
                    'error': 'Пустой запрос'
                }, status=400)

            if len(prompt) > 2000:  # Ограничение длины
                return JsonResponse({
                    'error': 'Промпт слишком длинный (максимум 2000 символов)'
                }, status=400)

            # Базовая санитизация
            prompt = prompt.replace('<', '&lt;').replace('>', '&gt;')
            logger.info(f"AI API: Промпт: {prompt[:100]}...")

            # Проверяем, что модель инициализирована
            if model is None:
                return JsonResponse({
                    'error': 'AI модель не инициализирована'
                }, status=500)

            # Получаем реальный ответ от Gemini API
            response = self.generate_ai_response(prompt)

            return JsonResponse(response)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON'
            }, status=400)
        except Exception as e:
            logger.error(f"AI API Error: {e}")
            return JsonResponse({
                'error': f'Внутренняя ошибка сервера: {str(e)}'
            }, status=500)

    def generate_ai_response(self, prompt):
        """
        Генерирует ответ ИИ на основе запроса через RAG-систему с кэшированием
        """
        try:
            # Создаем хеш для кэширования (используем SHA-256 для безопасности)
            prompt_hash = hashlib.sha256(prompt.lower().strip().encode()).hexdigest()
            cache_key = f"ai_response_{prompt_hash}"

            # Проверяем кэш
            cached_response = cache.get(cache_key)
            if cached_response:
                logger.info(
                    f"AI API: Используем кэшированный ответ для: {prompt[:50]}...")
                return cached_response

            # Пытаемся использовать RAG-систему
            try:
                from core.rag_system.orchestrator import AIOrchestrator
                orchestrator = AIOrchestrator()
                response_data = orchestrator.process_query(prompt)
                logger.info(f"AI API: Использована RAG-система для: {prompt[:50]}...")
            except Exception as rag_error:
                logger.warning(
                    f"RAG-система недоступна: {rag_error}, используем fallback")

                # Fallback на базовый Gemini API
                context = f"""Эксперт ЕГЭ. Отвечай кратко и по делу.

Вопрос: {prompt}

Ответ должен быть:
- Кратким и понятным
- С практическими примерами
- Соответствовать ЕГЭ
- Использовать Markdown

Отвечай быстро и структурированно."""

                # Получаем ответ от Gemini
                response = model.generate_content(context)
                answer = response.text

                # Определяем тему для практики
                practice_topic = self.detect_subject(prompt)

                # Формируем структурированный ответ
                response_data = {
                    'answer': answer,
                    'sources': self.get_sources_for_subject(practice_topic),
                    'practice': {
                        'topic': practice_topic,
                        'description': f'Практикуйтесь в решении задач по теме "{practice_topic}"'}}

            # Сохраняем в кэш на 1 час
            cache.set(cache_key, response_data, 3600)
            logger.info(f"AI API: Сохранили ответ в кэш для: {prompt[:50]}...")

            return response_data

        except Exception as e:
            logger.error(f"AI API Error: {e}")
            # Fallback на базовый ответ
            error_msg = (
                f"Извините, произошла ошибка при обработке вашего вопроса: {str(e)}. "
                f"Попробуйте переформулировать или обратитесь к официальным источникам.\n\n"
                f"Ваш вопрос: {prompt}")
            return {
                'answer': error_msg,
                'sources': [
                    {'title': 'ФИПИ - ЕГЭ', 'url': 'https://fipi.ru/ege'},
                    {'title': 'ExamFlow - Главная', 'url': 'https://examflow.ru/'}
                ],
                'practice': {
                    'topic': 'general',
                    'description': 'Выберите предмет для начала практики'
                }
            }

    def detect_subject(self, prompt):
        """
        Определяет предмет по запросу пользователя
        """
        prompt_lower = prompt.lower()

        subjects = {
            'mathematics': [
                'математик', 'алгебр', 'геометр', 'уравнен', 'функц', 'производн', 'интеграл'], 'russian': [
                'русск', 'сочинен', 'грамматик', 'орфограф', 'пунктуац'], 'physics': [
                'физик', 'механик', 'электричеств', 'оптик', 'термодинамик'], 'chemistry': [
                    'хими', 'органическ', 'неорганическ', 'молекул'], 'biology': [
                        'биолог', 'клетк', 'генетик', 'эволюц'], 'history': [
                            'истори', 'дата', 'событи', 'войн'], 'social_studies': [
                                'обществознан', 'полит', 'экономик', 'социолог'], 'english': [
                                    'английск', 'english', 'грамматик', 'vocabulary']}

        for subject, keywords in subjects.items():
            if any(keyword in prompt_lower for keyword in keywords):
                return subject

        return 'general'

    def get_sources_for_subject(self, subject):
        """
        Возвращает источники для конкретного предмета
        """
        sources_map = {
            'mathematics': [
                {'title': 'ФИПИ - Математика', 'url': 'https://fipi.ru/ege/matematika'},
                {'title': 'Открытый банк заданий', 'url': 'https://math-ege.sdamgia.ru/'}
            ],
            'russian': [
                {'title': 'ФИПИ - Русский язык', 'url': 'https://fipi.ru/ege/russkiy-yazyk'},
                {'title': 'Грамота.ру', 'url': 'https://gramota.ru/'}
            ],
            'physics': [
                {'title': 'ФИПИ - Физика', 'url': 'https://fipi.ru/ege/fizika'},
                {'title': 'Физика для всех', 'url': 'https://physics.ru/'}
            ],
            'chemistry': [
                {'title': 'ФИПИ - Химия', 'url': 'https://fipi.ru/ege/khimiya'},
                {'title': 'Химия для всех', 'url': 'https://chemistry.ru/'}
            ],
            'biology': [
                {'title': 'ФИПИ - Биология', 'url': 'https://fipi.ru/ege/biologiya'},
                {'title': 'Биология для всех', 'url': 'https://biology.ru/'}
            ],
            'history': [
                {'title': 'ФИПИ - История', 'url': 'https://fipi.ru/ege/istoriya'},
                {'title': 'История России', 'url': 'https://history.ru/'}
            ],
            'social_studies': [
                {'title': 'ФИПИ - Обществознание', 'url': 'https://fipi.ru/ege/obshchestvoznanie'},
                {'title': 'Обществознание', 'url': 'https://social.ru/'}
            ],
            'english': [
                {'title': 'ФИПИ - Английский язык', 'url': 'https://fipi.ru/ege/angliyskiy-yazyk'},
                {'title': 'Английский для ЕГЭ', 'url': 'https://english-ege.ru/'}
            ]
        }

        return sources_map.get(subject, [
            {'title': 'ФИПИ - ЕГЭ', 'url': 'https://fipi.ru/ege'},
            {'title': 'ExamFlow - Главная', 'url': 'https://examflow.ru/'}
        ])


class ProblemsAPI(View):
    """
    API для работы с задачами

    Обеспечивает:
    - Получение задач по темам
    - Проверку ответов
    - Отслеживание прогресса
    """

    def get(self, request: HttpRequest) -> JsonResponse:
        """
        GET запрос для получения задач по теме

        Параметры:
        - topic: тема предмета
        - limit: количество задач (по умолчанию 5)
        """
        topic = request.GET.get('topic', '')
        limit = int(request.GET.get('limit', 5))

        if not topic:
            return JsonResponse({
                'error': 'Не указана тема'
            }, status=400)

        # Здесь будет получение реальных задач из базы данных
        # Пока возвращаем заглушку
        problems = self.get_problems_by_topic(topic, limit)

        return JsonResponse({
            'topic': topic,
            'problems': problems,
            'total': len(problems)
        })

    def post(self, request: HttpRequest) -> JsonResponse:
        """
        POST запрос для проверки ответа

        Ожидает JSON:
        {
            "problem_id": "ID задачи",
            "answer": "Ответ пользователя"
        }
        """
        try:
            data = json.loads(request.body)
            problem_id = data.get('problem_id')
            answer = data.get('answer')

            if not problem_id or answer is None:
                return JsonResponse({
                    'error': 'Не указан ID задачи или ответ'
                }, status=400)

            # Здесь будет проверка ответа
            is_correct = self.check_answer(problem_id, answer)

            return JsonResponse({
                'problem_id': problem_id,
                'is_correct': is_correct,
                'feedback': self.get_feedback(is_correct)
            })

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON'
            }, status=400)

    def get_problems_by_topic(self, topic, limit):
        """
        Получает задачи по теме из реальной базы данных
        """
        try:
            from core.models import Task, Subject  # type: ignore

            # Получаем предмет по теме
            subject_mapping = {
                'mathematics': 'Математика',
                'russian': 'Русский язык',
                'physics': 'Физика',
                'chemistry': 'Химия',
                'biology': 'Биология',
                'history': 'История',
                'social_studies': 'Обществознание',
                'english': 'Английский язык'
            }

            subject_name = subject_mapping.get(topic, topic)

            # Получаем реальные задачи из базы данных
            tasks = Task.objects.filter(  # type: ignore
                subject__name__icontains=subject_name
            ).order_by('?')[:limit]  # Случайный порядок

            problems = []
            for task in tasks:
                problems.append({
                    'id': task.id,
                    'text': task.text,
                    'options': task.get_options_list(),
                    'correct_answer': task.correct_answer,
                    'hint': task.hint or 'Попробуйте внимательно прочитать условие задачи',
                    'explanation': task.explanation or 'Объяснение будет доступно после ответа'
                })

            return problems

        except ImportError:
            # Fallback если модели не доступны
            return self.get_fallback_problems(topic, limit)
        except Exception as e:
            logger.error(f"Error getting problems: {e}")
            return self.get_fallback_problems(topic, limit)

    def get_fallback_problems(self, topic, limit):
        """
        Fallback задачи если база данных недоступна
        """
        fallback_problems = {'mathematics': [{'id': 1,
                                              'text': 'Решите квадратное уравнение: x² - 5x + 6 = 0',
                                              'options': ['x₁ = 2, x₂ = 3',
                                                          'x₁ = -2, x₂ = -3',
                                                          'x₁ = 1, x₂ = 6',
                                                          'x₁ = -1, x₂ = -6'],
                                              'correct_answer': 0,
                                              'hint': 'Используйте формулу дискриминанта: D = b² - 4ac'},
                                             {'id': 2,
                                              'text': 'Найдите площадь круга с радиусом 5 см',
                                              'options': ['25π см²',
                                                          '50π см²',
                                                          '100π см²',
                                                          '125π см²'],
                                              'correct_answer': 0,
                                              'hint': 'Площадь круга: S = πr²'}],
                             'russian': [{'id': 3,
                                          'text': 'В каком предложении есть грамматическая ошибка?',
                                          'options': ['Он пришел домой поздно.',
                                                      'Мы с ним договорились о встрече.',
                                                      'По приезду в город мы сразу отправились в музей.',
                                                      'Дети играли во дворе.'],
                                          'correct_answer': 2,
                                          'hint': 'Правильно: "По приезде в город"'}]}

        return fallback_problems.get(topic, [])[:limit]

    def check_answer(self, problem_id, answer):
        """
        Проверяет правильность ответа по реальной базе данных
        """
        try:
            from core.models import Task  # type: ignore

            # Получаем задачу из базы данных
            task = Task.objects.get(id=problem_id)  # type: ignore

            # Проверяем ответ
            if hasattr(task, 'correct_answer'):
                return answer == task.correct_answer
            else:
                # Fallback проверка
                return answer == 0

        except Task.DoesNotExist:  # type: ignore
            logger.error(f"Task {problem_id} not found")
            return False
        except Exception as e:
            logger.error(f"Error checking answer: {e}")
            return False

    def get_feedback(self, is_correct):
        """
        Возвращает обратную связь в зависимости от правильности ответа
        """
        if is_correct:
            return "Отлично! Ответ правильный! 🎉"
        else:
            return "Попробуйте еще раз. Не отчаивайтесь! 💪"


class UserProfileAPI(View):
    """
    API для пользовательского профиля

    Обеспечивает:
    - Получение профиля пользователя
    - Обновление прогресса
    - Получение достижений
    """

    @method_decorator(login_required)
    def get(self, request: HttpRequest) -> JsonResponse:
        """
        GET запрос для получения профиля пользователя
        """
        user = request.user

        try:
            # Получаем реальные данные из базы
            from core.models import UserProfile, UserProgress  # type: ignore

            # Пытаемся получить профиль пользователя
            try:
                user_profile = UserProfile.objects.get(user=user)  # type: ignore
                level = user_profile.level
                xp = user_profile.xp
                total_problems_solved = user_profile.total_problems_solved
                streak = user_profile.streak
                achievements = user_profile.achievements.all() if hasattr(
                    user_profile, 'achievements') else []
            except UserProfile.DoesNotExist:  # type: ignore
                # Создаем базовый профиль если не существует
                level = 1
                xp = 0
                total_problems_solved = 0
                streak = 0
                achievements = []

            # Получаем прогресс по предметам
            subjects_progress = {}
            try:
                progress_entries = UserProgress.objects.filter(  # type: ignore
                    user=user)  # type: ignore
                for entry in progress_entries:
                    subjects_progress[entry.subject.name] = {
                        'problems_solved': entry.problems_solved,
                        'accuracy': entry.accuracy,
                        'last_activity': entry.last_activity.isoformat() if entry.last_activity else None
                    }
            except Exception:
                subjects_progress = {}

            profile = {
                'id': user.id,
                'username': user.username,
                'level': level,
                'xp': xp,
                'total_problems_solved': total_problems_solved,
                'streak': streak,
                'achievements': [
                    {
                        'name': a.name,
                        'description': a.description} for a in achievements] if achievements else [],
                'subjects_progress': subjects_progress}

            return JsonResponse(profile)

        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            # Fallback профиль
            profile = {
                'id': user.id,
                'username': user.username,
                'level': 1,
                'xp': 0,
                'total_problems_solved': 0,
                'streak': 0,
                'achievements': [],
                'subjects_progress': {}
            }
            return JsonResponse(profile)

    @method_decorator(login_required)
    def post(self, request: HttpRequest) -> JsonResponse:
        """
        POST запрос для обновления прогресса пользователя
        """
        try:
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'solve_problem':
                # Обновляем прогресс решения задачи
                problem_id = data.get('problem_id')
                is_correct = data.get('is_correct', False)
                subject = data.get('subject', 'general')

                return self.update_problem_progress(
                    request.user, problem_id, is_correct, subject)

            elif action == 'complete_challenge':
                # Обновляем прогресс челленджа
                challenge_id = data.get('challenge_id')
                return self.update_challenge_progress(request.user, challenge_id)

            else:
                return JsonResponse({
                    'error': 'Неизвестное действие'
                }, status=400)

        except json.JSONDecodeError:
            return JsonResponse({
                'error': 'Неверный JSON'
            }, status=400)

    def update_problem_progress(self, user, problem_id, is_correct, subject):
        """
        Обновляет прогресс решения задачи
        """
        try:
            from core.models import UserProfile, UserProgress  # type: ignore

            # Получаем или создаем профиль пользователя
            profile, created = UserProfile.objects.get_or_create(  # type: ignore
                user=user,
                defaults={
                    'level': 1,
                    'xp': 0,
                    'total_problems_solved': 0,
                    'streak': 0
                }
            )

            # Обновляем статистику
            if is_correct:
                profile.xp += 10
                profile.total_problems_solved += 1
                profile.streak += 1

                # Проверяем повышение уровня
                if profile.xp >= profile.level * 100:
                    profile.level += 1
                    profile.xp = 0

            profile.save()

            # Обновляем прогресс по предмету
            progress, created = UserProgress.objects.get_or_create(  # type: ignore
                user=user,
                subject__name=subject,
                defaults={
                    'problems_solved': 0,
                    'correct_answers': 0,
                    'accuracy': 0.0
                }
            )

            progress.problems_solved += 1
            if is_correct:
                progress.correct_answers += 1

            progress.accuracy = (progress.correct_answers /
                                 progress.problems_solved) * 100
            progress.save()

            return JsonResponse({
                'status': 'success',
                'new_level': profile.level,
                'new_xp': profile.xp,
                'total_solved': profile.total_problems_solved,
                'streak': profile.streak
            })

        except Exception as e:
            logger.error(f"Error updating problem progress: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    def update_challenge_progress(self, user, challenge_id):
        """
        Обновляет прогресс челленджа
        """
        try:
            from core.models import UserProfile  # type: ignore

            profile, created = UserProfile.objects.get_or_create(  # type: ignore
                user=user,
                defaults={
                    'level': 1,
                    'xp': 0,
                    'total_problems_solved': 0,
                    'streak': 0
                }
            )

            # Бонус за выполнение челленджа
            profile.xp += 50
            profile.save()

            return JsonResponse({
                'status': 'success',
                'challenge_completed': True,
                'xp_gained': 50
            })

        except Exception as e:
            logger.error(f"Error updating challenge progress: {e}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


# URL маршруты для API
@csrf_exempt
@require_http_methods(["POST"])
def ai_chat_api(request):
    """
    API endpoint для чата с ИИ

    Обрабатывает POST запросы к /ai/api/chat/
    """
    logger.info(f"AI Chat API: Получен запрос от {request.META.get('REMOTE_ADDR')}")
    logger.info(f"AI Chat API: Метод: {request.method}")
    logger.info(f"AI Chat API: Headers: {dict(request.headers)}")

    try:
        view = AIAssistantAPI()
        return view.post(request)
    except Exception as e:
        logger.error(f"AI Chat API Error: {e}")
        return JsonResponse({
            'error': f'Внутренняя ошибка сервера: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["GET", "POST"])
def problems_api(request):
    """
    API endpoint для работы с задачами

    Обрабатывает GET и POST запросы к /api/problems/
    """
    view = ProblemsAPI()
    if request.method == 'GET':
        return view.get(request)
    else:
        return view.post(request)


@require_http_methods(["GET", "POST"])
def user_profile_api(request):
    """
    API endpoint для пользовательского профиля

    Обрабатывает GET и POST запросы к /api/user/profile/
    """
    view = UserProfileAPI()
    if request.method == 'GET':
        return view.get(request)
    else:
        return view.post(request)
