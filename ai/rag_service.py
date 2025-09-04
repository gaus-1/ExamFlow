"""
RAG (Retrieval Augmented Generation) система для ExamFlow

Система для:
1. Поиска похожих заданий
2. Анализа сложности
3. Персонализации обучения
4. Генерации контекстных ответов
"""

import logging
from typing import List, Dict, Any, Optional
from django.db.models import Q
from django.contrib.auth.models import User

from learning.models import Task, Subject, UserProgress
from authentication.models import UserProfile


logger = logging.getLogger(__name__)


class RAGService:
    """Сервис для RAG функциональности в ExamFlow"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def find_similar_tasks(self, task: Task, limit: int = 5) -> List[Task]:
        """
        Находит похожие задания по темам и сложности
        
        Args:
            task: Исходное задание
            limit: Максимальное количество похожих заданий
            
        Returns:
            Список похожих заданий
        """
        try:
            # Получаем темы исходного задания
            task_topics = set(task.topics.all())  # type: ignore
            
            # Ищем задания по темам и сложности
            similar_tasks = Task.objects.filter(  # type: ignore
                Q(topics__in=task_topics) &  # Похожие темы
                Q(subject=task.subject),      # Тот же предмет
                Q(difficulty__gte=max(1, task.difficulty - 1)) &  # Сложность ±1
                Q(difficulty__lte=min(5, task.difficulty + 1))
            ).exclude(
                id=task.id  # Исключаем само задание
            ).distinct()
            
            # Сортируем по релевантности (количество общих тем)
            def relevance_score(t):
                common_topics = len(set(t.topics.all()) & task_topics)
                difficulty_diff = abs(t.difficulty - task.difficulty)
                return (common_topics * 10) - difficulty_diff
            
            sorted_tasks = sorted(similar_tasks, key=relevance_score, reverse=True)
            
            return sorted_tasks[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка при поиске похожих заданий: {e}")
            return []
    
    def analyze_student_progress(self, user: User, subject: Optional[Subject] = None) -> Dict[str, Any]:
        """
        Анализирует прогресс ученика
        
        Args:
            user: Пользователь
            subject: Предмет (если None, анализируем все)
            
        Returns:
            Словарь с анализом прогресса
        """
        try:
            # Получаем профиль пользователя
            profile, _ = UserProfile.objects.get_or_create(user=user)
            
            # Базовый фильтр по предмету
            base_filter = Q(user=user)
            if subject:
                base_filter &= Q(task__subject=subject)
            
            # Получаем прогресс
            progress = UserProgress.objects.filter(base_filter)
            
            # Статистика
            total_tasks = progress.count()
            correct_tasks = progress.filter(is_correct=True).count()
            accuracy = (correct_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            # Анализ по сложности
            difficulty_stats = {}
            for difficulty in range(1, 6):
                diff_tasks = progress.filter(task__difficulty=difficulty)
                diff_correct = diff_tasks.filter(is_correct=True).count()
                diff_total = diff_tasks.count()
                
                if diff_total > 0:
                    difficulty_stats[difficulty] = {
                        'total': diff_total,
                        'correct': diff_correct,
                        'accuracy': (diff_correct / diff_total * 100)
                    }
            
            # Анализ по темам
            topic_stats = {}
            for progress_item in progress:
                for topic in progress_item.task.topics.all():
                    if topic.name not in topic_stats:
                        topic_stats[topic.name] = {'total': 0, 'correct': 0}
                    
                    topic_stats[topic.name]['total'] += 1
                    if progress_item.is_correct:
                        topic_stats[topic.name]['correct'] += 1
            
            # Вычисляем точность по темам
            for topic_name, stats in topic_stats.items():
                stats['accuracy'] = (stats['correct'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            # Определяем слабые и сильные стороны
            weak_topics = [name for name, stats in topic_stats.items() if stats['accuracy'] < 60]
            strong_topics = [name for name, stats in topic_stats.items() if stats['accuracy'] >= 80]
            
            # Рекомендации по сложности
            recommended_difficulty = 1
            for diff in range(1, 6):
                if diff in difficulty_stats and difficulty_stats[diff]['accuracy'] >= 70:
                    recommended_difficulty = diff + 1
                else:
                    break
            
            return {
                'total_tasks': total_tasks,
                'correct_tasks': correct_tasks,
                'accuracy': round(accuracy, 1),
                'difficulty_stats': difficulty_stats,
                'topic_stats': topic_stats,
                'weak_topics': weak_topics,
                'strong_topics': strong_topics,
                'recommended_difficulty': min(recommended_difficulty, 5),
                'can_solve_tasks': profile.can_solve_tasks,
                'daily_limit': profile.daily_tasks_limit,
                'tasks_solved_today': profile.tasks_solved_today
            }
            
        except Exception as e:
            self.logger.error(f"Ошибка при анализе прогресса: {e}")
            return {}
    
    def generate_personalized_prompt(self, user: User, task: Task, task_type: str = 'task_explanation') -> str:
        """
        Генерирует персонализированный промпт для AI
        
        Args:
            user: Пользователь
            task: Задание
            task_type: Тип задачи (task_explanation, hint_generation, etc.)
            
        Returns:
            Персонализированный промпт
        """
        try:
            # Анализируем прогресс ученика
            progress_analysis = self.analyze_student_progress(user, task.subject)
            
            # Формируем контекст о задании
            task_context = f"""
ЗАДАНИЕ:
Предмет: {task.subject.name}
Темы: {', '.join([t.name for t in task.topics.all()])} 
Сложность: {task.difficulty}/5 
Текст: {task.text[:500]}... 
"""
            
            # Формируем контекст о прогрессе ученика
            progress_context = f"""
ПРОГРЕСС УЧЕНИКА:
Общая точность: {progress_analysis.get('accuracy', 0)}%
Решено заданий: {progress_analysis.get('total_tasks', 0)}
Рекомендуемая сложность: {progress_analysis.get('recommended_difficulty', 1)}/5

Слабые темы: {', '.join(progress_analysis.get('weak_topics', [])[:3])}
Сильные темы: {', '.join(progress_analysis.get('strong_topics', [])[:3])}
"""
            
            # Формируем персонализированный промпт
            if task_type == 'task_explanation':
                prompt = f"""
{task_context}

{progress_context}

ИНСТРУКЦИЯ:
Объясни решение этого задания, учитывая уровень ученика.
Если это сложная тема для ученика - объясни подробнее.
Если ученик силен в этой теме - можешь дать более продвинутые советы.
"""
            elif task_type == 'hint_generation':
                prompt = f"""
{task_context}

{progress_context}

ИНСТРУКЦИЯ:
Дай подсказку для решения, учитывая уровень ученика.
Если тема слабая - дай более подробную подсказку.
Если тема сильная - можешь дать более тонкую подсказку.
"""
            elif task_type == 'personalized_learning':
                prompt = f"""
{task_context}

{progress_context}

ИНСТРУКЦИЯ:
Дай персональные рекомендации для этого ученика:
1. Что нужно повторить перед решением
2. На что обратить внимание
3. Как избежать типичных ошибок
4. План дальнейшего изучения
"""
            else:
                prompt = f"{task_context}\n\n{progress_context}\n\nОбъясни это задание."
            
            return prompt.strip()
            
        except Exception as e:
            self.logger.error(f"Ошибка при генерации персонализированного промпта: {e}")
            return f"Объясни это задание: {task.text[:300]}..."
    
    def get_learning_recommendations(self, user: User, subject: Optional[Subject] = None) -> List[Dict[str, Any]]:
        """
        Получает рекомендации по обучению
        
        Args:
            user: Пользователь
            subject: Предмет
            
        Returns:
            Список рекомендаций
        """
        try:
            # Анализируем прогресс
            progress = self.analyze_student_progress(user, subject)
            
            recommendations = []
            
            # Рекомендации по слабым темам
            for weak_topic in progress.get('weak_topics', [])[:3]:
                recommendations.append({
                    'type': 'weak_topic',
                    'title': f'Повторить тему: {weak_topic}',
                    'description': f'Ваша точность в теме "{weak_topic}" ниже 60%. Рекомендуем повторить материал.',
                    'priority': 'high',
                    'action': 'review_topic'
                })
            
            # Рекомендации по сложности
            current_diff = progress.get('recommended_difficulty', 1)
            if current_diff < 5:
                recommendations.append({
                    'type': 'difficulty',
                    'title': f'Попробовать сложность {current_diff}',
                    'description': f'Вы готовы к заданиям сложности {current_diff}/5. Попробуйте более сложные задачи!',
                    'priority': 'medium',
                    'action': 'increase_difficulty'
                })
            
            # Рекомендации по ежедневной практике
            if progress.get('tasks_solved_today', 0) < 3:
                recommendations.append({
                    'type': 'daily_practice',
                    'title': 'Ежедневная практика',
                    'description': 'Решайте хотя бы 3 задания в день для лучшего прогресса.',
                    'priority': 'medium',
                    'action': 'daily_practice'
                })
            
            # Рекомендации по сильным темам
            for strong_topic in progress.get('strong_topics', [])[:2]:
                recommendations.append({
                    'type': 'strong_topic',
                    'title': f'Отлично в теме: {strong_topic}',
                    'description': f'Вы отлично знаете "{strong_topic}"! Можете помогать другим ученикам.',
                    'priority': 'low',
                    'action': 'help_others'
                })
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении рекомендаций: {e}")
            return []
    
    def search_tasks_by_query(self, query: str, subject: Optional[Subject] = None, 
                             difficulty_range: Optional[tuple] = None, 
                             limit: int = 10) -> List[Task]:
        """
        Поиск заданий по текстовому запросу
        
        Args:
            query: Поисковый запрос
            subject: Предмет
            difficulty_range: Диапазон сложности (min, max)
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных заданий
        """
        try:
            # Базовый фильтр
            tasks = Task.objects.all()
            
            # Фильтр по предмету
            if subject:
                tasks = tasks.filter(subject=subject)
            
            # Фильтр по сложности
            if difficulty_range:
                min_diff, max_diff = difficulty_range
                tasks = tasks.filter(difficulty__gte=min_diff, difficulty__lte=max_diff)
            
            # Поиск по тексту и темам
            search_filter = (
                Q(text__icontains=query) |
                Q(title__icontains=query) |
                Q(topics__name__icontains=query)
            )
            
            tasks = tasks.filter(search_filter).distinct()
            
            # Сортируем по релевантности
            def relevance_score(task):
                score = 0
                if query.lower() in task.title.lower():
                    score += 10
                if query.lower() in task.text.lower():
                    score += 5
                for topic in task.topics.all():
                    if query.lower() in topic.name.lower():
                        score += 8
                return score
            
            sorted_tasks = sorted(tasks, key=relevance_score, reverse=True)
            
            return sorted_tasks[:limit]
            
        except Exception as e:
            self.logger.error(f"Ошибка при поиске заданий: {e}")
            return []


# Создаем глобальный экземпляр сервиса
rag_service = RAGService()
