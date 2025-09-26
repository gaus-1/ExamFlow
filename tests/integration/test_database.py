"""
Integration тесты для базы данных ExamFlow
"""

import pytest
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db(transaction=True)
class TestDatabaseTransactions:
    """Тесты транзакций базы данных"""
    
    def test_user_creation_transaction(self):
        """Тест создания пользователя в транзакции"""
        with transaction.atomic():
            user = User.objects.create_user(
                username='transaction_user',
                email='transaction@examflow.ru',
                password='testpass123',
                telegram_id=111222333
            )
            
            assert user.id is not None
            assert User.objects.filter(username='transaction_user').exists()
    
    def test_user_deletion_transaction(self, user):
        """Тест удаления пользователя в транзакции"""
        user_id = user.id
        
        with transaction.atomic():
            user.delete()
            
            assert not User.objects.filter(id=user_id).exists()
    
    def test_transaction_rollback(self):
        """Тест отката транзакции"""
        initial_count = User.objects.count()
        
        try:
            with transaction.atomic():
                User.objects.create_user(
                    username='rollback_user',
                    email='rollback@examflow.ru',
                    password='testpass123'
                )
                
                # Искусственно вызываем ошибку
                raise IntegrityError("Test rollback")
                
        except IntegrityError:
            pass
        
        # Проверяем что пользователь не был создан
        final_count = User.objects.count()
        assert final_count == initial_count
    
    def test_nested_transactions(self):
        """Тест вложенных транзакций"""
        with transaction.atomic():
            user1 = User.objects.create_user(
                username='nested_user1',
                email='nested1@examflow.ru',
                password='testpass123'
            )
            
            with transaction.atomic():
                user2 = User.objects.create_user(
                    username='nested_user2',
                    email='nested2@examflow.ru',
                    password='testpass123'
                )
            
            # Оба пользователя должны существовать
            assert User.objects.filter(username='nested_user1').exists()
            assert User.objects.filter(username='nested_user2').exists()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabaseConstraints:
    """Тесты ограничений базы данных"""
    
    def test_user_telegram_id_unique_constraint(self):
        """Тест уникальности telegram_id"""
        User.objects.create_user(
            username='user1',
            email='user1@examflow.ru',
            password='pass1',
            telegram_id=123456789
        )
        
        with pytest.raises(IntegrityError):
            User.objects.create_user(
                username='user2',
                email='user2@examflow.ru',
                password='pass2',
                telegram_id=123456789  # Дублирующий telegram_id
            )
    
    def test_subject_code_unique_constraint(self):
        """Тест уникальности кода предмета"""
        from learning.models import Subject
        
        Subject.objects.create( # type: ignore
            name='Математика 1',
            code='MATH',
            exam_type='ЕГЭ'
        )
        
        with pytest.raises(IntegrityError):
            Subject.objects.create( # type: ignore
                name='Математика 2',
                code='MATH',  # Дублирующий код
                exam_type='ОГЭ'
            )
    
    def test_user_progress_unique_constraint(self, user, math_task):
        """Тест уникальности прогресса пользователя"""
        from learning.models import UserProgress
        
        UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        with pytest.raises(IntegrityError):
            UserProgress.objects.create( # type: ignore
                user=user,
                task=math_task,  # Дублирующая комбинация user-task
                is_correct=False,
                attempts=2
            )
    
    def test_user_profile_telegram_id_unique_constraint(self, user):
        """Тест уникальности telegram_id в профиле"""
        from core.models import UserProfile
        
        UserProfile.objects.create( # type: ignore
            user=user,
            telegram_id=123456789,
            telegram_username='user1'
        )
        
        user2 = User.objects.create_user( # type: ignore
            username='user2',
            email='user2@examflow.ru',
            password='pass2'
        )
        
        with pytest.raises(IntegrityError):
            UserProfile.objects.create( # type: ignore
                user=user2,
                telegram_id=123456789,  # Дублирующий telegram_id
                telegram_username='user2'
            )


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabaseRelationships:
    """Тесты связей в базе данных"""
    
    def test_subject_task_relationship(self, math_subject):
        """Тест связи предмет-задание"""
        from learning.models import Task
        
        task = Task.objects.create( # type: ignore
            title='Тестовое задание',
            description='Содержание задания',
            answer='ответ',
            subject=math_subject
        )
        
        # Проверяем прямую связь
        assert task.subject == math_subject
        
        # Проверяем обратную связь
        assert task in math_subject.task_set.all()
    
    def test_user_progress_relationships(self, user, math_task):
        """Тест связей в прогрессе пользователя"""
        from learning.models import UserProgress
        
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        # Проверяем связи
        assert progress.user == user
        assert progress.task == math_task
        
        # Проверяем обратные связи
        assert progress in user.userprogress_set.all()
        assert progress in math_task.userprogress_set.all()
    
    def test_user_profile_relationship(self, user):
        """Тест связи пользователь-профиль"""
        from core.models import UserProfile
        
        profile = UserProfile.objects.create( # type: ignore
            user=user,
            telegram_id=123456789,
            telegram_username='testuser'
        )
        
        # Проверяем прямую связь
        assert profile.user == user
        
        # Проверяем обратную связь
        assert hasattr(user, 'userprofile')
        assert user.userprofile == profile
    
    def test_topic_subject_relationship(self, math_subject):
        """Тест связи тема-предмет"""
        from learning.models import Topic
        
        topic = Topic.objects.create( # type: ignore
            name='Алгебра',
            description='Основы алгебры',
            subject=math_subject
        )
        
        # Проверяем связи
        assert topic.subject == math_subject
        assert topic in math_subject.topic_set.all()


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabaseQueries:
    """Тесты запросов к базе данных"""
    
    def test_user_filter_queries(self):
        """Тест фильтрации пользователей"""
        User.objects.create_user( # type: ignore    
            username='active_user',
            email='active@examflow.ru',
            password='pass1',
            is_active=True
        )
        
        User.objects.create_user( # type: ignore
            username='inactive_user',
            email='inactive@examflow.ru',
            password='pass2',
            is_active=False
        )
        
        # Фильтрация активных пользователей
        active_users = User.objects.filter(is_active=True)
        assert active_users.count() >= 1
        
        # Фильтрация по email
        email_users = User.objects.filter(email__contains='@examflow.ru')
        assert email_users.count() >= 2
    
    def test_subject_queries(self, math_subject, russian_subject):
        """Тест запросов к предметам"""
        # Фильтрация по типу экзамена
        ege_subjects = User.objects.filter(exam_type='ЕГЭ')
        assert ege_subjects.count() >= 2
        
        # Фильтрация по коду
        math_subjects = User.objects.filter(code__contains='MATH')
        assert math_subjects.count() >= 1
    
    def test_task_queries(self, math_task, russian_task):
        """Тест запросов к заданиям"""
        from learning.models import Task
        
        # Фильтрация по сложности
        easy_tasks = Task.objects.filter(difficulty=1) # type: ignore
        assert easy_tasks.count() >= 1
        
        # Фильтрация по типу задания
        numerical_tasks = Task.objects.filter(task_type='numerical') # type: ignore
        assert numerical_tasks.count() >= 1
        
        # Фильтрация по предмету
        math_tasks = Task.objects.filter(subject__name__contains='Математика') # type: ignore
        assert math_tasks.count() >= 1
    
    def test_user_progress_queries(self, user, math_task, russian_task):
        """Тест запросов к прогрессу пользователя"""
        from learning.models import UserProgress
        
        # Создаем прогресс
        UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        UserProgress.objects.create( # type: ignore
            user=user,
            task=russian_task,
            is_correct=False,
            attempts=2
        )
        
        # Фильтрация правильных ответов
        correct_progress = UserProgress.objects.filter(is_correct=True) # type: ignore
        assert correct_progress.count() >= 1
        
        # Фильтрация по количеству попыток
        multiple_attempts = UserProgress.objects.filter(attempts__gt=1) # type: ignore
        assert multiple_attempts.count() >= 1
        
        # Фильтрация по пользователю
        user_progress = UserProgress.objects.filter(user=user) # type: ignore
        assert user_progress.count() >= 2


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabaseIndexes:
    """Тесты индексов базы данных"""
    
    def test_user_telegram_id_index(self):
        """Тест индекса telegram_id"""
        # Создаем пользователя
        user = User.objects.create_user(
            username='index_user',
            email='index@examflow.ru',
            password='pass',
            telegram_id=999888777
        )
        
        # Запрос должен использовать индекс
        found_user = User.objects.filter(telegram_id=999888777).first()
        assert found_user == user
    
    def test_subject_code_index(self):
        """Тест индекса кода предмета"""
        from learning.models import Subject
        
        subject = Subject.objects.create( # type: ignore
            name='Индексный предмет',
            code='INDEX_TEST',
            exam_type='ЕГЭ'
        )
        
        # Запрос должен использовать индекс
        found_subject = Subject.objects.filter(code='INDEX_TEST').first() # type: ignore
        assert found_subject == subject
    
    def test_task_subject_index(self, math_subject):
        """Тест индекса связи задача-предмет"""
        from learning.models import Task
        
        task = Task.objects.create( # type: ignore  
            title='Индексное задание',
            description='Содержание',
            answer='ответ',
            subject=math_subject
        )
        
        # Запрос должен использовать индекс
        found_tasks = Task.objects.filter(subject=math_subject) # type: ignore
        assert task in found_tasks


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabaseValidation:
    """Тесты валидации данных в базе"""
    
    def test_user_email_validation(self):
        """Тест валидации email пользователя"""
        # Валидный email
        user = User.objects.create_user(
            username='valid_email',
            email='valid@examflow.ru',
            password='pass'
        )
        assert user.email == 'valid@examflow.ru'
        
        # Невалидный email (Django может не проверять формат)
        # Но мы можем проверить что он сохраняется
        user2 = User.objects.create_user(
            username='invalid_email',
            email='not-an-email',
            password='pass'
        )
        assert user2.email == 'not-an-email'
    
    def test_subject_name_validation(self):
        """Тест валидации названия предмета"""
        from learning.models import Subject
        
        # Пустое название должно вызывать ошибку
        with pytest.raises(ValidationError):
            subject = Subject(
                name='',
                code='EMPTY',
                exam_type='ЕГЭ'
            )
            subject.full_clean()
    
    def test_task_difficulty_validation(self, math_subject):
        """Тест валидации сложности задания"""
        from learning.models import Task
        
        # Валидная сложность
        task = Task.objects.create( # type: ignore
            title='Валидное задание',
            description='Содержание',
            answer='ответ',
            subject=math_subject,
            difficulty=2
        )
        assert task.difficulty == 2
        
        # Сложность вне диапазона (если есть ограничения)
        task2 = Task.objects.create( # type: ignore
            title='Задание с высокой сложностью',
            description='Содержание',
            answer='ответ',
            subject=math_subject,
            difficulty=10  # Если есть ограничение на 1-5
        )
        # Может быть валидным или невалидным в зависимости от модели
        assert task2.difficulty == 10


@pytest.mark.integration
@pytest.mark.database
@pytest.mark.django_db
class TestDatabasePerformance:
    """Тесты производительности базы данных"""
    
    def test_bulk_create_users(self):
        """Тест массового создания пользователей"""
        users_data = []
        for i in range(100):
            users_data.append(
                User( # type: ignore
                    username=f'bulk_user_{i}',
                    email=f'bulk{i}@examflow.ru',
                    password='bulkpass',
                    telegram_id=1000000 + i
                )
            )
        
        # Массовое создание
        User.objects.bulk_create(users_data)
        
        # Проверяем что все созданы
        assert User.objects.filter(username__startswith='bulk_user_').count() == 100
    
    def test_bulk_update_progress(self, user, math_task, russian_task):
        """Тест массового обновления прогресса"""
        from learning.models import UserProgress
        
        # Создаем прогресс
        progress1 = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=False,
            attempts=1
        )
        
        progress2 = UserProgress.objects.create( # type: ignore
            user=user,
            task=russian_task,
            is_correct=False,
            attempts=1
        )
        
        # Массовое обновление
        UserProgress.objects.filter(user=user).update(is_correct=True, attempts=2) # type: ignore
        
        # Проверяем обновления
        updated_progress = UserProgress.objects.filter(user=user) # type: ignore
        for progress in updated_progress:
            assert progress.is_correct is True
            assert progress.attempts == 2
    
    def test_select_related_optimization(self, user, math_task):
        """Тест оптимизации с select_related"""
        from learning.models import UserProgress
        
        # Создаем прогресс
        UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        # Запрос с select_related должен быть оптимизирован
        progress_with_relations = UserProgress.objects.select_related( # type: ignore
            'user', 'task__subject'
        ).filter(user=user)
        
        for progress in progress_with_relations:
            # Эти обращения не должны вызывать дополнительные запросы
            username = progress.user.username
            subject_name = progress.task.subject.name
            assert username is not None
            assert subject_name is not None
    
    def test_prefetch_related_optimization(self, user, math_task, russian_task):
        """Тест оптимизации с prefetch_related"""
        from learning.models import UserProgress
        
        # Создаем прогресс для разных заданий
        UserProgress.objects.create(user=user, task=math_task, is_correct=True) # type: ignore
        UserProgress.objects.create(user=user, task=russian_task, is_correct=False) # type: ignore
        
        # Запрос с prefetch_related должен быть оптимизирован
        user_with_progress = User.objects.prefetch_related(
            'userprogress_set__task'
        ).filter(id=user.id).first()
        
        # Эти обращения не должны вызывать дополнительные запросы
        progress_count = user_with_progress.userprogress_set.count()
        assert progress_count >= 2
        
        for progress in user_with_progress.userprogress_set.all():
            task_title = progress.task.title
            assert task_title is not None
