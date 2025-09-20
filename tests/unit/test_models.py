"""
Unit тесты для моделей ExamFlow
"""

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from learning.models import Subject, Task, Topic, UserProgress
from core.models import UserProfile
from learning.models import Achievement
from ai.models import AiLimit

User = get_user_model()


@pytest.mark.unit
@pytest.mark.django_db
class TestUserModel:
    """Тесты модели пользователя"""
    
    def test_create_user(self):
        """Тест создания обычного пользователя"""
        user = User.objects.create_user(
            telegram_id=123456789,
            telegram_username='testuser',
            telegram_first_name='Test',
            telegram_last_name='User'
        )
        
        assert user.telegram_id == 123456789
        assert user.telegram_username == 'testuser'
        assert user.telegram_first_name == 'Test'
        assert user.telegram_last_name == 'User'
        assert user.is_active is True
        assert user.is_staff is False
        assert user.is_superuser is False
    
    def test_create_superuser(self):
        """Тест создания суперпользователя"""
        admin = User.objects.create_superuser(
            telegram_id=987654321,
            telegram_username='admin',
            telegram_first_name='Admin'
        )
        
        assert admin.is_superuser is True
        assert admin.is_staff is True
        assert admin.is_active is True
        assert admin.telegram_id == 987654321
    
    def test_user_str_representation(self, user):
        """Тест строкового представления пользователя"""
        assert 'testuser' in str(user) or str(user.telegram_id) in str(user)
    
    def test_user_telegram_id_unique(self):
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


@pytest.mark.unit
@pytest.mark.django_db
class TestSubjectModel:
    """Тесты модели предмета"""
    
    def test_create_subject(self):
        """Тест создания предмета"""
        subject = Subject.objects.create( # type: ignore
            name='Математика (профильная)',
            code='MATH_PRO',
            exam_type='ЕГЭ',
            description='Профильная математика ЕГЭ',
            icon='📐'
        )
        
        assert subject.name == 'Математика (профильная)'
        assert subject.code == 'MATH_PRO'
        assert subject.exam_type == 'ЕГЭ'
    
    def test_subject_str_representation(self, math_subject):
        """Тест строкового представления предмета"""
        assert str(math_subject) == f'{math_subject.name} ({math_subject.get_exam_type_display()})'
    
    def test_subject_code_unique(self):
        """Тест уникальности кода предмета"""
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
    
    def test_subject_exam_types(self):
        """Тест различных типов экзаменов"""
        ege_subject = Subject.objects.create( # type: ignore
            name='Физика ЕГЭ',
            code='PHYS_EGE',
            exam_type='ЕГЭ'
        )
        
        oge_subject = Subject.objects.create(  # type: ignore
            name='Физика ОГЭ',
            code='PHYS_OGЕ',
            exam_type='ОГЭ'
        )
        
        assert ege_subject.exam_type == 'ЕГЭ'
        assert oge_subject.exam_type == 'ОГЭ'


@pytest.mark.unit
@pytest.mark.django_db
class TestTaskModel:
    """Тесты модели задания"""
    
    def test_create_task(self, math_subject):
        """Тест создания задания"""
        task = Task.objects.create( # type: ignore
            title='Решите уравнение',
            description='Решите уравнение: 2x + 5 = 13',
            answer='4',
            subject=math_subject,
            difficulty=2
        )
        
        assert task.title == 'Решите уравнение'
        assert task.description == 'Решите уравнение: 2x + 5 = 13'
        assert task.answer == '4'
        assert task.subject == math_subject
        assert task.difficulty == 2
    
    def test_task_str_representation(self, math_task):
        """Тест строкового представления задания"""
        assert str(math_task) == math_task.title
    
    def test_task_difficulty_levels(self, math_subject):
        """Тест различных уровней сложности"""
        easy_task = Task.objects.create( # type: ignore
            title='Легкое задание',
            description='Простое уравнение',
            answer='1',
            subject=math_subject,
            difficulty=1
        )
        
        hard_task = Task.objects.create( # type: ignore
            title='Сложное задание',
            description='Сложное уравнение',
            answer='3',
            subject=math_subject,
            difficulty=3
        )
        
        assert easy_task.difficulty == 1
        assert hard_task.difficulty == 3
    
    def test_task_subject_relationship(self, math_subject, russian_subject):
        """Тест связи задания с предметом"""
        math_task = Task.objects.create( # type: ignore
            title='Математическое задание',
            description='2 + 2 = ?',
            answer='4',
            subject=math_subject,
            difficulty=1
        )
        
        russian_task = Task.objects.create( # type: ignore
            title='Задание по русскому',
            description='Вставьте букву',
            answer='о',
            subject=russian_subject,
            difficulty=1
        )
        
        assert math_task.subject == math_subject
        assert russian_task.subject == russian_subject


@pytest.mark.unit
@pytest.mark.django_db
class TestUserProgressModel:
    """Тесты модели прогресса пользователя"""
    
    def test_create_user_progress(self, user, math_task):
        """Тест создания прогресса пользователя"""
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            user_answer='4',
            is_correct=True,
            attempts=1
        )
        
        assert progress.user == user
        assert progress.task == math_task
        assert progress.user_answer == '4'
        assert progress.is_correct is True
        assert progress.attempts == 1
    
    def test_user_progress_str_representation(self, user, math_task):
        """Тест строкового представления прогресса"""
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        expected = f"{user.username} - {math_task.subject.name}"
        assert str(progress) == expected
    
    def test_user_progress_update(self, user, math_task):
        """Тест обновления прогресса пользователя"""
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=False,
            attempts=1
        )
        
        # Обновляем прогресс
        progress.is_correct = True
        progress.attempts = 2
        progress.save()
        
        updated_progress = UserProgress.objects.get(id=progress.id) # type: ignore
        assert updated_progress.is_correct is True
        assert updated_progress.attempts == 2
    
    def test_unique_user_task_progress(self, user, math_task):
        """Тест уникальности прогресса пользователя по заданию"""
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


@pytest.mark.unit
@pytest.mark.django_db
class TestUserProfileModel:
    """Тесты модели профиля пользователя"""
    
    def test_create_user_profile(self, user):
        """Тест создания профиля пользователя"""
        profile = UserProfile.objects.create( # type: ignore
            user=user
        )
        
        assert profile.user == user
    
    def test_user_profile_str_representation(self, user):
        """Тест строкового представления профиля"""
        profile = UserProfile.objects.create( # type: ignore
            user=user
        )
        
        assert str(profile) == f'Профиль {user.username}'
    
    def test_user_profile_unique_per_user(self, user):
        """Тест уникальности профиля для пользователя"""
        UserProfile.objects.create( # type: ignore
            user=user
        )
        
        with pytest.raises(IntegrityError):
            UserProfile.objects.create( # type: ignore
                user=user  # Дублирующий пользователь
            )


@pytest.mark.unit
@pytest.mark.django_db
class TestAiLimitModel:
    """Тесты модели лимитов AI"""
    
    def test_create_ai_limit(self, user):
        """Тест создания лимита AI"""
        limit = AiLimit.objects.create( # type: ignore
            user=user,
            limit_type='daily',
            current_usage=0,
            max_limit=100
        )
        
        assert limit.user == user
        assert limit.limit_type == 'daily'
        assert limit.current_usage == 0
        assert limit.max_limit == 100
    
    def test_ai_limit_str_representation(self, user):
        """Тест строкового представления лимита"""
        limit = AiLimit.objects.create( # type: ignore
            user=user,
            limit_type='daily',
            current_usage=5,
            max_limit=100
        )
        
        expected = f'{user.username} - daily: 5/100'
        assert str(limit) == expected
    
    def test_ai_limit_is_exceeded(self, user):
        """Тест проверки превышения лимита"""
        limit = AiLimit.objects.create( # type: ignore
            user=user,
            limit_type='daily',
            current_usage=100,
            max_limit=100
        )
        
        assert limit.is_exceeded() is True
        
        limit.current_usage = 50
        assert limit.is_exceeded() is False
    
    def test_ai_limit_can_make_request(self, user):
        """Тест возможности сделать запрос"""
        limit = AiLimit.objects.create( # type: ignore
            user=user,
            limit_type='daily',
            current_usage=50,
            max_limit=100
        )
        
        assert limit.can_make_request() is True
        
        limit.current_usage = 100
        assert limit.can_make_request() is False


@pytest.mark.unit
@pytest.mark.django_db
class TestTopicModel:
    """Тесты модели темы"""
    
    def test_create_topic(self, math_subject):
        """Тест создания темы"""
        topic = Topic.objects.create( # type: ignore
            name='Алгебра',
            subject=math_subject,
            code='ALGEBRA'
        )
        
        assert topic.name == 'Алгебра'
        assert topic.subject == math_subject
        assert topic.code == 'ALGEBRA'
    
    def test_topic_str_representation(self, math_subject):
        """Тест строкового представления темы"""
        topic = Topic.objects.create( # type: ignore
            name='Алгебра',
            subject=math_subject,
            code='ALGEBRA'
        )
        
        assert str(topic) == f'{math_subject.name} - Алгебра'
    
    def test_topic_subject_relationship(self, math_subject, russian_subject):
        """Тест связи темы с предметом"""
        math_topic = Topic.objects.create( # type: ignore
            name='Алгебра',
            subject=math_subject,
            code='ALGEBRA'
        )
        
        russian_topic = Topic.objects.create( # type: ignore
            name='Орфография',
            subject=russian_subject,
            code='ORPHO'
        )
        
        assert math_topic.subject == math_subject
        assert russian_topic.subject == russian_subject


@pytest.mark.unit
@pytest.mark.django_db
class TestAchievementModel:
    """Тесты модели достижения"""
    
    def test_create_achievement(self):
        """Тест создания достижения"""
        achievement = Achievement.objects.create( # type: ignore
            name='Первое задание',
            description='Решите первое задание',
            icon='🎯',
            points_required=10
        )
        
        assert achievement.name == 'Первое задание'
        assert achievement.description == 'Решите первое задание'
        assert achievement.icon == '🎯'
        assert achievement.points_required == 10
    
    def test_achievement_str_representation(self):
        """Тест строкового представления достижения"""
        achievement = Achievement.objects.create( # type: ignore
            name='Первое задание',
            description='Решите первое задание'
        )
        
        assert str(achievement) == 'Первое задание'
