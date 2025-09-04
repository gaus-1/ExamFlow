"""
Улучшенный AI-сервис с интеграцией персонализации
"""

import logging
from typing import Dict, List, Any
from django.contrib.auth.models import User
from core.personalization_system import get_user_insights
from ai.services import AiService

logger = logging.getLogger(__name__)


class PersonalizedAiService:
    """AI-сервис с персонализацией для ExamFlow"""

    def __init__(self):
        self.ai_service = AiService()

    def get_personalized_response(self,
                                  prompt: str,
                                  user: User,
                                  task=None,
                                  context_type: str = 'general') -> Dict[str,
                                                                         Any]:
        """Получает персонализированный ответ от AI"""
        try:
            # Получаем персональные данные пользователя
            user_insights = get_user_insights(getattr(user, 'id', 1))

            # Формируем персонализированный промпт
            enhanced_prompt = self._enhance_prompt_with_context(
                prompt, user_insights, context_type, task)

            # Получаем базовый ответ от AI
            if task:
                try:
                    ai_response = self.ai_service.ask_with_rag(
                        enhanced_prompt, user, task, context_type)
                except Exception as e:
                    logger.warning(f"RAG ошибка, используем обычный запрос: {e}")
                    ai_response = self.ai_service.ask(enhanced_prompt, user)
            else:
                ai_response = self.ai_service.ask(enhanced_prompt, user)

            if 'error' in ai_response:
                return {
                    'success': False,
                    'error': ai_response['error'],
                    'response': f"❌ Ошибка: {ai_response['error']}"
                }

            # Обогащаем ответ персонализированными рекомендациями
            enhanced_response = self._enhance_response_with_personalization(
                ai_response['response'], user_insights, context_type, task
            )

            return {
                'success': True, 'response': enhanced_response, 'provider': ai_response.get(
                    'provider', 'AI'), 'personalization_data': {
                    'progress_summary': user_insights.get(
                        'progress_summary', {}), 'weak_topics': user_insights.get(
                        'weak_topics', [])[
                        :3], 'recommendations': self._get_context_recommendations(
                            user_insights, context_type, task)}}

        except Exception as e:
            logger.error(f"Ошибка в PersonalizedAiService: {e}")
            return {
                'success': False,
                'error': str(e),
                'response': f"❌ Произошла ошибка при получении персонализированного ответа: {str(e)}"}

    def _enhance_prompt_with_context(
            self,
            prompt: str,
            user_insights: Dict,
            context_type: str,
            task=None) -> str:
        """Обогащает промпт контекстной информацией о пользователе"""

        enhanced_prompt = prompt

        # Добавляем информацию о прогрессе
        progress = user_insights.get('progress_summary', {})
        if progress:
            enhanced_prompt += f"\n\nКонтекст о пользователе:\n"
            enhanced_prompt += f"- Решено заданий: {progress.get('solved_tasks', 0)}\n"
            enhanced_prompt += f"- Общая точность: {progress.get('success_rate', 0)}%\n"

        # Добавляем информацию о слабых темах
        weak_topics = user_insights.get('weak_topics', [])
        if weak_topics:
            enhanced_prompt += f"\nСлабые темы пользователя:\n"
            for topic in weak_topics[:3]:
                enhanced_prompt += f"- {topic.get('subject', 'Неизвестно')}: "
                enhanced_prompt += f"{topic.get('failed_tasks', 0)} проваленных заданий\n"

        # Добавляем предпочтения
        preferences = user_insights.get('preferences', {})
        if preferences.get('favorite_subjects'):
            enhanced_prompt += f"\nЛюбимые предметы: {', '.join(preferences['favorite_subjects'])}\n"

        # Добавляем контекст типа запроса
        if context_type == 'task_help':
            enhanced_prompt += "\n\nИнструкция: Объясни решение простыми словами, "
            enhanced_prompt += "учитывая текущий уровень пользователя."

        elif context_type == 'topic_explanation':
            enhanced_prompt += "\n\nИнструкция: Объясни тему с учетом того, "
            enhanced_prompt += "что пользователь может испытывать трудности в этой области."

        return enhanced_prompt

    def _enhance_response_with_personalization(
            self,
            ai_response: str,
            user_insights: Dict,
            context_type: str,
            task=None) -> str:
        """Обогащает ответ AI персонализированными рекомендациями"""

        enhanced_response = ai_response

        # Добавляем персональные рекомендации
        if context_type == 'task_help' and task:
            enhanced_response += "\n\n🎯 **Персональные рекомендации для вас:**\n"

            # Рекомендации по сложности
            preferences = user_insights.get('preferences', {})
            difficulty_pref = preferences.get('difficulty_preference', 3)

            if hasattr(task, 'difficulty') and task.difficulty > difficulty_pref + 1:
                enhanced_response += "• Это задание выше вашего текущего уровня. "
                enhanced_response += "Рекомендую сначала потренироваться на более простых заданиях.\n"

        # Добавляем мотивационные элементы
        progress = user_insights.get('progress_summary', {})
        if progress:
            success_rate = progress.get('success_rate', 0)
            if success_rate >= 80:
                enhanced_response += "\n🎉 **Отличная работа!** Вы показываете высокие результаты.\n"
            elif success_rate >= 60:
                enhanced_response += "\n👍 **Хороший прогресс!** Вы на правильном пути.\n"
            else:
                enhanced_response += "\n💪 **Не сдавайтесь!** Каждое задание - это шаг к успеху.\n"

        # Добавляем следующие шаги
        enhanced_response += "\n📚 **Что делать дальше:**\n"
        enhanced_response += "• Решите еще несколько заданий по этой теме\n"
        enhanced_response += "• Используйте наши рекомендации для практики\n"
        enhanced_response += "• Отслеживайте свой прогресс в разделе 'Персонализация'\n"

        return enhanced_response

    def _get_context_recommendations(
            self,
            user_insights: Dict,
            context_type: str,
            task=None) -> List[Dict]:
        """Получает контекстные рекомендации"""

        recommendations = []

        # Общие рекомендации по обучению
        weak_topics = user_insights.get('weak_topics', [])
        if weak_topics:
            for topic in weak_topics[:2]:
                recommendations.append({
                    'type': 'weak_topic',
                    'title': f"Поработать над темой: {topic.get('subject', 'Неизвестно')}",
                    'description': f"Провалено {topic.get('failed_tasks', 0)} заданий",
                    'action': "Решить задания по этой теме"
                })

        # Рекомендации по сложности
        preferences = user_insights.get('preferences', {})
        difficulty_pref = preferences.get('difficulty_preference', 3)

        if difficulty_pref < 4:
            recommendations.append({
                'type': 'difficulty',
                'title': "Попробовать более сложные задания",
                'description': f"Ваш текущий уровень: {difficulty_pref}/5",
                'action': "Выбрать задания сложности 4-5"
            })

        return recommendations
