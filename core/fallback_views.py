"""
Fallback views для работы без базы данных на Render
"""

import json
import logging

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name="dispatch")
class FallbackAIView(View):
    """Fallback AI API для работы без БД"""

    def post(self, request):
        try:
            data = json.loads(request.body or "{}")
            query = data.get("query", "").strip()

            if not query:
                return JsonResponse(
                    {
                        "success": True,
                        "answer": "Пожалуйста, задайте вопрос по математике или русскому языку для ЕГЭ/ОГЭ.",
                        "sources": [],
                    },
                    status=200,
                )

            # Прямое обращение к Gemini без БД
            try:
                import google.generativeai as genai
                from django.conf import settings

                api_key = getattr(settings, "GEMINI_API_KEY", "")
                if api_key:
                    genai.configure(api_key=api_key)  # type: ignore
                    model = genai.GenerativeModel("gemini-1.5-flash")  # type: ignore

                    system_prompt = """Ты - ExamFlow AI, эксперт по подготовке к ЕГЭ и ОГЭ.

Специализируешься на:
📐 Математике (профильная и базовая, ОГЭ) - уравнения, функции, геометрия, алгебра
📝 Русском языке (ЕГЭ и ОГЭ) - грамматика, орфография, сочинения, литература

Стиль общения:
- Краткий и конкретный ответ (до 400 слов)
- Пошаговые решения для математики
- Примеры и образцы для русского языка
- НЕ упоминай провайдера ИИ
"""

                    full_prompt = f"{system_prompt}\n\nВопрос: {query}"
                    response = model.generate_content(full_prompt)

                    if response.text:
                        answer = response.text.strip()
                    else:
                        answer = "Не удалось получить ответ. Попробуйте переформулировать вопрос."
                else:
                    answer = "API ключ не настроен. Обратитесь к администратору."

            except Exception as e:
                logger.error(f"Ошибка Gemini API: {e}")
                answer = "Сервис временно недоступен. Попробуйте позже."

            return JsonResponse(
                {"success": True, "answer": answer, "sources": []}, status=200
            )

        except Exception as e:
            logger.error(f"Ошибка в FallbackAIView: {e}")
            return JsonResponse(
                {
                    "success": True,
                    "answer": "Я ExamFlow AI! Задайте вопрос по математике или русскому языку для ЕГЭ/ОГЭ.",
                    "sources": [],
                },
                status=200,
            )


def fallback_subjects_view(request):
    """Fallback view для предметов без БД"""
    try:
        # Статичные данные для fallback режима
        math_subjects = [
            {
                "id": 1,
                "name": "Математика (профильная)",
                "description": "ЕГЭ профильная математика",
            },
            {
                "id": 2,
                "name": "Математика (базовая)",
                "description": "ЕГЭ базовая математика",
            },
            {"id": 3, "name": "Математика (ОГЭ)", "description": "ОГЭ математика"},
        ]

        russian_subjects = [
            {"id": 4, "name": "Русский язык (ЕГЭ)", "description": "ЕГЭ русский язык"},
            {"id": 5, "name": "Русский язык (ОГЭ)", "description": "ОГЭ русский язык"},
        ]

        context = {
            "math_subjects": math_subjects,
            "russian_subjects": russian_subjects,
            "total_subjects": len(math_subjects) + len(russian_subjects),
            "focus_message": "Специализируемся на математике и русском языке (режим без БД)",
        }
        return render(request, "learning/focused_subjects.html", context)

    except Exception as e:
        logger.error(f"Ошибка в fallback_subjects_view: {e}")
        context = {
            "math_subjects": [],
            "russian_subjects": [],
            "total_subjects": 0,
            "focus_message": "Сервис временно недоступен. Попробуйте позже.",
        }
        return render(request, "learning/focused_subjects.html", context)
