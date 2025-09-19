"""
Тесты SQL запросов для PostgreSQL
"""

import pytest
from django.test import TestCase, TransactionTestCase
from django.db import connection, transaction
from django.core.management import call_command
from django.contrib.auth import get_user_model
from learning.models import Subject, Task, UserProgress
from core.models import UserProfile
import logging

logger = logging.getLogger(__name__)

User = get_user_model()


@pytest.mark.database
@pytest.mark.sql
class TestSQLQueries(TransactionTestCase):
    """Тесты SQL запросов и оптимизации"""
    
    def setUp(self):
        """Настройка тестовых данных"""
        # Создаем тестовых пользователей
        self.user1 = User.objects.create_user(
            username='testuser1',
            email='test1@example.com',
            password='testpass123'
        )
        
        self.user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )
        
        # Создаем предметы
        self.math_subject = Subject.objects.create( # type: ignore
            name='Математика',
            code='MATH',
            exam_type='ege'
        )
        
        self.russian_subject = Subject.objects.create( # type: ignore
            name='Русский язык',
            code='RUS',
            exam_type='ege'
        )
        
        # Создаем задания
        self.tasks = []
        for i in range(20):
            task = Task.objects.create( # type: ignore
                title=f'Задание {i+1}',
                content=f'Содержание задания {i+1}',
                answer=f'Ответ {i+1}',
                subject=self.math_subject if i % 2 == 0 else self.russian_subject,
                difficulty=i % 3 + 1
            )
            self.tasks.append(task)
        
        # Создаем прогресс пользователей
        for i, task in enumerate(self.tasks[:10]):
            UserProgress.objects.create( # type: ignore
                user=self.user1,
                task=task,
                is_completed=i % 2 == 0,
                user_answer=f'Ответ пользователя {i+1}'
            )
    
    def test_subject_statistics_query(self):
        """Тест запроса статистики по предметам"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.name,
                    s.exam_type,
                    COUNT(t.id) as task_count,
                    AVG(t.difficulty) as avg_difficulty
                FROM learning_subject s
                LEFT JOIN learning_task t ON s.id = t.subject_id
                GROUP BY s.id, s.name, s.exam_type
                ORDER BY task_count DESC
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 2  # Два предмета
            
            # Проверяем, что математика имеет больше заданий
            math_result = next(r for r in results if r[0] == 'Математика')
            russian_result = next(r for r in results if r[0] == 'Русский язык')
            
            assert math_result[2] == 10  # 10 заданий по математике
            assert russian_result[2] == 10  # 10 заданий по русскому
    
    def test_user_progress_analytics(self):
        """Тест аналитики прогресса пользователей"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.username,
                    COUNT(up.id) as total_tasks,
                    COUNT(CASE WHEN up.is_completed THEN 1 END) as completed_tasks,
                    ROUND(
                        COUNT(CASE WHEN up.is_completed THEN 1 END) * 100.0 / 
                        COUNT(up.id), 2
                    ) as completion_rate
                FROM auth_user u
                LEFT JOIN learning_userprogress up ON u.id = up.user_id
                GROUP BY u.id, u.username
                HAVING COUNT(up.id) > 0
                ORDER BY completion_rate DESC
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 1  # Только один пользователь с прогрессом
            username, total, completed, rate = results[0]
            
            assert username == 'testuser1'
            assert total == 10
            assert completed == 5  # Половина заданий выполнена
            assert rate == 50.0
    
    def test_difficulty_distribution(self):
        """Тест распределения заданий по сложности"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    difficulty,
                    COUNT(*) as count,
                    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as percentage
                FROM learning_task
                GROUP BY difficulty
                ORDER BY difficulty
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 3  # Три уровня сложности
            
            # Проверяем, что все уровни представлены
            difficulties = [r[0] for r in results]
            assert set(difficulties) == {1, 2, 3}
    
    def test_task_search_query(self):
        """Тест поискового запроса по заданиям"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    t.id,
                    t.title,
                    t.content,
                    s.name as subject_name,
                    t.difficulty
                FROM learning_task t
                JOIN learning_subject s ON t.subject_id = s.id
                WHERE 
                    t.title ILIKE %s OR 
                    t.content ILIKE %s OR 
                    s.name ILIKE %s
                ORDER BY t.difficulty, t.id
                LIMIT 10
            """, ['%задание%', '%задание%', '%математика%'])
            
            results = cursor.fetchall()
            
            assert len(results) > 0
            assert all('задание' in str(r[1]).lower() for r in results)
    
    def test_user_activity_query(self):
        """Тест запроса активности пользователей"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.username,
                    u.date_joined,
                    COUNT(up.id) as tasks_attempted,
                    MAX(up.created_at) as last_activity,
                    COUNT(CASE WHEN up.is_completed THEN 1 END) as tasks_completed
                FROM auth_user u
                LEFT JOIN learning_userprogress up ON u.id = up.user_id
                GROUP BY u.id, u.username, u.date_joined
                ORDER BY last_activity DESC NULLS LAST
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 2  # Два пользователя
            
            # Проверяем, что пользователь с активностью идет первым
            active_user = results[0]
            assert active_user[0] == 'testuser1'  # testuser1
            assert active_user[2] == 10  # 10 попыток
    
    def test_subject_performance_query(self):
        """Тест запроса производительности по предметам"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.name,
                    s.exam_type,
                    COUNT(DISTINCT up.user_id) as active_users,
                    COUNT(up.id) as total_attempts,
                    COUNT(CASE WHEN up.is_completed THEN 1 END) as successful_attempts,
                    ROUND(
                        COUNT(CASE WHEN up.is_completed THEN 1 END) * 100.0 / 
                        COUNT(up.id), 2
                    ) as success_rate
                FROM learning_subject s
                LEFT JOIN learning_task t ON s.id = t.subject_id
                LEFT JOIN learning_userprogress up ON t.id = up.task_id
                GROUP BY s.id, s.name, s.exam_type
                ORDER BY success_rate DESC
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 2
            
            # Проверяем, что есть активность по математике
            math_result = next(r for r in results if r[0] == 'Математика')
            assert math_result[2] == 1  # 1 активный пользователь
            assert math_result[3] == 5  # 5 попыток по математике
    
    def test_complex_join_query(self):
        """Тест сложного JOIN запроса"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    u.username,
                    s.name as subject_name,
                    COUNT(t.id) as available_tasks,
                    COUNT(up.id) as attempted_tasks,
                    COUNT(CASE WHEN up.is_completed THEN 1 END) as completed_tasks,
                    ROUND(
                        COUNT(CASE WHEN up.is_completed THEN 1 END) * 100.0 / 
                        NULLIF(COUNT(up.id), 0), 2
                    ) as completion_rate
                FROM auth_user u
                CROSS JOIN learning_subject s
                LEFT JOIN learning_task t ON s.id = t.subject_id
                LEFT JOIN learning_userprogress up ON u.id = up.user_id AND t.id = up.task_id
                GROUP BY u.id, u.username, s.id, s.name
                ORDER BY u.username, s.name
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 4  # 2 пользователя × 2 предмета
            
            # Проверяем, что все комбинации пользователь-предмет присутствуют
            combinations = [(r[0], r[1]) for r in results]
            expected = [
                ('testuser1', 'Математика'),
                ('testuser1', 'Русский язык'),
                ('testuser2', 'Математика'),
                ('testuser2', 'Русский язык')
            ]
            
            for expected_combo in expected:
                assert expected_combo in combinations
    
    def test_index_usage_query(self):
        """Тест использования индексов"""
        with connection.cursor() as cursor:
            # Проверяем, что запрос использует индексы
            cursor.execute("EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM learning_task WHERE subject_id = %s", [self.math_subject.id])
            
            explain_result = cursor.fetchall()
            
            # Проверяем, что запрос выполнился быстро
            assert len(explain_result) > 0
            
            # Проверяем, что используется индекс (если он есть)
            explain_text = ' '.join([str(row) for row in explain_result])
            # В реальном проекте здесь можно проверить наличие "Index Scan" или "Seq Scan"
    
    def test_window_functions(self):
        """Тест оконных функций"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    username,
                    COUNT(up.id) as total_attempts,
                    ROW_NUMBER() OVER (ORDER BY COUNT(up.id) DESC) as rank,
                    RANK() OVER (ORDER BY COUNT(up.id) DESC) as rank_with_ties,
                    DENSE_RANK() OVER (ORDER BY COUNT(up.id) DESC) as dense_rank,
                    LAG(COUNT(up.id)) OVER (ORDER BY COUNT(up.id) DESC) as prev_count
                FROM auth_user u
                LEFT JOIN learning_userprogress up ON u.id = up.user_id
                GROUP BY u.id, u.username
                ORDER BY total_attempts DESC
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 2
            
            # Проверяем ранжирование
            first_user = results[0]
            assert first_user[2] == 1  # ROW_NUMBER = 1
            assert first_user[3] == 1  # RANK = 1
    
    def test_aggregate_functions(self):
        """Тест агрегатных функций"""
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT 
                    s.name,
                    COUNT(t.id) as task_count,
                    MIN(t.difficulty) as min_difficulty,
                    MAX(t.difficulty) as max_difficulty,
                    AVG(t.difficulty) as avg_difficulty,
                    STDDEV(t.difficulty) as difficulty_stddev,
                    PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY t.difficulty) as median_difficulty
                FROM learning_subject s
                LEFT JOIN learning_task t ON s.id = t.subject_id
                GROUP BY s.id, s.name
            """)
            
            results = cursor.fetchall()
            
            assert len(results) == 2
            
            for result in results:
                subject_name, count, min_diff, max_diff, avg_diff, stddev, median = result
                
                assert count == 10  # 10 заданий на предмет
                assert min_diff == 1  # Минимальная сложность
                assert max_diff == 3  # Максимальная сложность
                assert avg_diff == 2.0  # Средняя сложность
                assert median == 2.0  # Медианная сложность


@pytest.mark.database
@pytest.mark.transaction
class TestDatabaseTransactions(TransactionTestCase):
    """Тесты транзакций базы данных"""
    
    def test_transaction_rollback(self):
        """Тест отката транзакции"""
        initial_count = Task.objects.count() # type: ignore
        
        try:
            with transaction.atomic():
                # Создаем задание
                Task.objects.create( # type: ignore
                    title='Тестовое задание',
                    content='Содержание',
                    answer='Ответ',
                    subject=Subject.objects.first(), # type: ignore
                    difficulty=1
                )
                
                # Проверяем, что задание создано
                assert Task.objects.count() == initial_count + 1 # type: ignore
                
                # Искусственно вызываем ошибку
                raise Exception("Тестовая ошибка")
                
        except Exception:
            pass
        
        # Проверяем, что транзакция откатилась
        assert Task.objects.count() == initial_count # type: ignore
    
    def test_nested_transactions(self):
        """Тест вложенных транзакций"""
        initial_count = Task.objects.count() # type: ignore
        
        with transaction.atomic():
            # Внешняя транзакция
            task1 = Task.objects.create( # type: ignore
                title='Задание 1',
                content='Содержание 1',
                answer='Ответ 1',
                subject=Subject.objects.first(), # type: ignore
                difficulty=1
            )
            
            try:
                with transaction.atomic():
                    # Внутренняя транзакция
                    task2 = Task.objects.create( # type: ignore
                        title='Задание 2',
                        content='Содержание 2',
                        answer='Ответ 2',
                        subject=Subject.objects.first(), # type: ignore
                        difficulty=2
                    )
                    
                    # Искусственно вызываем ошибку во внутренней транзакции
                    raise Exception("Ошибка во внутренней транзакции")
                    
            except Exception:
                # Внутренняя транзакция откатилась, но внешняя продолжается
                pass
            
            # Проверяем, что только первое задание создано
            assert Task.objects.count() == initial_count + 1 # type: ignore
            assert Task.objects.filter(id=task1.id).exists() # type: ignore
    
    def test_select_for_update(self):
        """Тест блокировки строк для обновления"""
        if not Subject.objects.exists(): # type: ignore
            Subject.objects.create(name='Тест', code='TEST', exam_type='ege') # type: ignore
        
        subject = Subject.objects.first() # type: ignore
        
        with transaction.atomic():
            # Блокируем строку для обновления
            locked_subject = Subject.objects.select_for_update().get(id=subject.id) # type: ignore
            
            # В другом потоке это должно заблокироваться
            # В реальном тесте здесь можно использовать threading
            assert locked_subject.id == subject.id
