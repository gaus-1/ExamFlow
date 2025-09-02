"""
Мозговой центр - центральный сервис для обработки запросов
"""

import logging
import google.generativeai as genai
from typing import Dict, List, Optional
from django.conf import settings
from django.utils import timezone
from django.db import models

from core.rag_system.vector_store import VectorStore
from core.models import UnifiedProfile # type: ignore

logger = logging.getLogger(__name__)

class AIOrchestrator:
    """
    Центральный сервис для обработки запросов пользователей
    """
    
    def __init__(self):
        self.vector_store = VectorStore()
        
        # Настраиваем Gemini API
        genai.configure(api_key=settings.GEMINI_API_KEY)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def process_query(self, query: str, user_id: Optional[int] = None) -> Dict:
        """
        Обрабатывает запрос пользователя
        """
        try:
            logger.info(f"Обрабатываем запрос: {query[:100]}...")
            
            # 1. Выполняем семантический поиск
            search_results = self.vector_store.search(query, limit=5)
            
            # 2. Получаем контекст пользователя
            user_context = self.get_user_context(user_id) if user_id else {}
            
            # 3. Формируем контекст для генерации ответа
            context = self.build_context(search_results, user_context)
            
            # 4. Генерируем промпт
            prompt = self.generate_prompt(query, context, user_context)
            
            # 5. Получаем ответ от языковой модели
            ai_response = self.get_ai_response(prompt)
            
            # 6. Обрабатываем ответ
            processed_response = self.process_ai_response(ai_response, search_results)
            
            # 7. Обновляем прогресс пользователя
            if user_id:
                self.update_user_progress(user_id, query, processed_response)
            
            logger.info("Запрос обработан успешно")
            return processed_response
            
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            return self.get_fallback_response(query, str(e))
    
    def get_user_context(self, user_id: int) -> Dict:
        """
        Получает контекст пользователя
        """
        try:
            # Пытаемся найти профиль по user_id (Django User) или telegram_id
            user_profile = UnifiedProfile.objects.filter( # type: ignore
                models.Q(user_id=user_id) | models.Q(telegram_id=user_id)
            ).first()
            
            if not user_profile:
                return {}
            
            return {
                'level': user_profile.level,
                'xp': user_profile.experience_points,
                'total_problems_solved': user_profile.total_solved,
                'streak': user_profile.current_streak,
                'achievements': user_profile.achievements,
                'preferred_subjects': [s.name for s in user_profile.preferred_subjects.all()]
            }
            
        except Exception as e:
            logger.error(f"Ошибка при получении контекста пользователя: {e}")
            return {}
    
    def build_context(self, search_results: List[Dict], user_context: Dict) -> str:
        """
        Формирует контекст из результатов поиска
        """
        if not search_results:
            return "Релевантная информация не найдена."
        
        context_parts = ["Релевантная информация из базы знаний ФИПИ:"]
        
        for i, result in enumerate(search_results, 1):
            context_parts.append(f"\n{i}. {result['text']}")
            context_parts.append(f"   Источник: {result['source_title']}")
            context_parts.append(f"   Предмет: {result['subject']}")
            context_parts.append(f"   Релевантность: {result['similarity']:.2f}")
        
        return "\n".join(context_parts)
    
    def generate_prompt(self, query: str, context: str, user_context: Dict) -> str:
        """
        Генерирует промпт для языковой модели
        """
        prompt_parts = [
            "Ты - эксперт по подготовке к ЕГЭ в России. Отвечай на вопросы учеников, используя предоставленную информацию из официальных источников ФИПИ.",
            "",
            f"Вопрос ученика: {query}",
            "",
            "Контекст из базы знаний:",
            context,
            ""
        ]
        
        # Добавляем персональную информацию, если есть
        if user_context:
            prompt_parts.extend([
                "Информация о пользователе:",
                f"- Уровень: {user_context.get('level', 'неизвестен')}",
                f"- Решено задач: {user_context.get('total_problems_solved', 0)}",
                f"- Серия правильных ответов: {user_context.get('streak', 0)}",
                ""
            ])
        
        prompt_parts.extend([
            "Требования к ответу:",
            "1. Отвечай кратко и по делу",
            "2. Используй информацию из контекста",
            "3. Если информации недостаточно, честно скажи об этом",
            "4. Предложи практические задания по теме",
            "5. Используй Markdown для форматирования",
            "6. Укажи источники информации",
            "",
            "Ответ:"
        ])
        
        return "\n".join(prompt_parts)
    
    def get_ai_response(self, prompt: str) -> str:
        """
        Получает ответ от языковой модели
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Ошибка при получении ответа от AI: {e}")
            return f"Извините, произошла ошибка при генерации ответа: {str(e)}"
    
    def process_ai_response(self, ai_response: str, search_results: List[Dict]) -> Dict:
        """
        Обрабатывает ответ от AI и формирует структурированный ответ
        """
        # Извлекаем источники
        sources = []
        for result in search_results:
            sources.append({
                'title': result['source_title'],
                'url': result['source_url'],
                'type': result['source_type'],
                'subject': result['subject'],
                'relevance': result['similarity']
            })
        
        # Определяем тему для практики
        practice_topic = self.detect_practice_topic(ai_response, search_results)
        
        return {
            'answer': ai_response,
            'sources': sources,
            'practice': {
                'topic': practice_topic,
                'description': f'Практикуйтесь в решении задач по теме "{practice_topic}"'
            },
            'generated_at': timezone.now().isoformat()
        }
    
    def detect_practice_topic(self, response: str, search_results: List[Dict]) -> str:
        """
        Определяет тему для практики
        """
        if search_results:
            # Берем предмет из наиболее релевантного результата
            best_result = max(search_results, key=lambda x: x['similarity'])
            return best_result['subject'] or 'general'
        
        # Пытаемся определить по тексту ответа
        response_lower = response.lower()
        
        subjects = {
            'mathematics': ['математик', 'алгебр', 'геометр', 'уравнен', 'функц'],
            'russian': ['русск', 'сочинен', 'грамматик', 'орфограф'],
            'physics': ['физик', 'механик', 'электричеств', 'оптик'],
            'chemistry': ['хими', 'органическ', 'неорганическ'],
            'biology': ['биолог', 'клетк', 'генетик', 'эволюц'],
            'history': ['истори', 'дата', 'событи', 'войн'],
            'social_studies': ['обществознан', 'полит', 'экономик'],
            'english': ['английск', 'english', 'грамматик']
        }
        
        for subject, keywords in subjects.items():
            if any(keyword in response_lower for keyword in keywords):
                return subject
        
        return 'general'
    
    def update_user_progress(self, user_id: int, query: str, response: Dict):
        """
        Обновляет прогресс пользователя
        """
        try:
            from core.models import UserProfile, UserProgress, Subject # type: ignore
            
            # Получаем или создаем профиль пользователя
            user_profile, created = UserProfile.objects.get_or_create(
                user_id=user_id,
                defaults={
                    'level': 1,
                    'xp': 0,
                    'total_problems_solved': 0,
                    'streak': 0
                }
            )
            
            # Добавляем XP за использование AI
            user_profile.xp += 5
            user_profile.save()
            
            # Обновляем прогресс по предмету
            practice_topic = response['practice']['topic']
            if practice_topic != 'general':
                subject, _ = Subject.objects.get_or_create(name=practice_topic) # type: ignore
                
                progress, _ = UserProgress.objects.get_or_create( # type: ignore
                    user_id=user_id,
                    subject=subject,
                    defaults={
                        'problems_solved': 0,
                        'correct_answers': 0,
                        'accuracy': 0.0
                    }
                )
                
                # Обновляем статистику
                progress.last_activity = timezone.now()
                progress.save()
            
            logger.info(f"Обновлен прогресс пользователя {user_id}")
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении прогресса: {e}")
    
    def get_fallback_response(self, query: str, error: str) -> Dict:
        """
        Возвращает fallback ответ в случае ошибки
        """
        return {
            'answer': f"Извините, произошла ошибка при обработке вашего вопроса: {error}. Попробуйте переформулировать вопрос или обратитесь к официальным источникам ФИПИ.",
            'sources': [
                {'title': 'ФИПИ - ЕГЭ', 'url': 'https://fipi.ru/ege'},
                {'title': 'ExamFlow - Главная', 'url': 'https://examflow.ru/'}
            ],
            'practice': {
                'topic': 'general',
                'description': 'Выберите предмет для начала практики'
            },
            'generated_at': timezone.now().isoformat(),
            'error': error
        }
