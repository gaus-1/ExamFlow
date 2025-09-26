"""
Глобальные фикстуры для тестирования ExamFlow
"""

import os
import shutil
import tempfile
from unittest.mock import Mock, patch

import django
import pytest
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

# Настройка Django для тестов
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "examflow_project.settings")
django.setup()

User = get_user_model()


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    """Настройка базы данных для тестов"""
    with django_db_blocker.unblock():
        pass


@pytest.fixture
def client():
    """Django test client"""
    return Client()


@pytest.fixture
def user():
    """Создание тестового пользователя"""
    user = User.objects.create_user(
        telegram_id=123456789,
        telegram_username="testuser",
        telegram_first_name="Test",
        telegram_last_name="User",
    )
    return user


@pytest.fixture
def admin_user():
    """Создание тестового администратора"""
    admin = User.objects.create_superuser(
        telegram_id=987654321, telegram_username="admin", telegram_first_name="Admin"
    )
    return admin


@pytest.fixture
def authenticated_client(client, user):
    """Аутентифицированный клиент"""
    client.force_login(user)
    return client


@pytest.fixture
def authenticated_admin_client(client, admin_user):
    """Аутентифицированный админ-клиент"""
    client.force_login(admin_user)
    return client


@pytest.fixture
def temp_media_root():
    """Временная папка для медиа файлов"""
    temp_dir = tempfile.mkdtemp()
    old_media_root = settings.MEDIA_ROOT
    settings.MEDIA_ROOT = temp_dir
    yield temp_dir
    settings.MEDIA_ROOT = old_media_root
    shutil.rmtree(temp_dir)


@pytest.fixture
def mock_redis():
    """Мок Redis для тестов"""
    with patch("django.core.cache.cache") as mock_cache:
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        mock_cache.delete.return_value = True
        yield mock_cache


@pytest.fixture
def mock_ai_service():
    """Мок AI сервиса"""
    with patch("core.container.Container.ai_orchestrator") as mock_ai:
        mock_orchestrator = Mock()
        mock_orchestrator.ask.return_value = {
            "answer": "Тестовый ответ от AI",
            "sources": [
                {"title": "Тестовый источник", "content": "Тестовое содержание"}
            ],
        }
        mock_ai.return_value = mock_orchestrator
        yield mock_orchestrator


@pytest.fixture
def mock_telegram_bot():
    """Мок Telegram бота"""
    with patch("telegram_bot.bot_main.get_bot") as mock_bot:
        mock_bot_instance = Mock()
        mock_bot.return_value = mock_bot_instance
        yield mock_bot_instance


@pytest.fixture
def math_subject():
    """Создание предмета Математика"""
    from learning.models import Subject

    return Subject.objects.create(  # type: ignore
        name="Математика (профильная)",
        code="MATH_PRO",
        exam_type="ЕГЭ",
        description="Профильная математика ЕГЭ",
        icon="📐",
        is_primary=True,
    )


@pytest.fixture
def russian_subject():
    """Создание предмета Русский язык"""
    from learning.models import Subject

    return Subject.objects.create(  # type: ignore
        name="Русский язык",
        code="RUSSIAN",
        exam_type="ЕГЭ",
        description="Русский язык ЕГЭ",
        icon="📝",
        is_primary=True,
    )


@pytest.fixture
def math_task(math_subject):
    """Создание задания по математике"""
    from learning.models import Task

    return Task.objects.create(  # type: ignore
        title="Решите уравнение",
        description="Решите уравнение: 2x + 5 = 13",
        answer="4",
        subject=math_subject,
        difficulty=2,
    )


@pytest.fixture
def russian_task(russian_subject):
    """Создание задания по русскому языку"""
    from learning.models import Task

    return Task.objects.create(  # type: ignore
        title="Вставьте пропущенную букву",
        description='В слове "в...рона" пропущена буква:',
        answer="о",
        subject=russian_subject,
        difficulty=1,
    )


@pytest.fixture
def user_profile(user):
    """Создание профиля пользователя"""
    from core.models import UserProfile

    return UserProfile.objects.create(  # type: ignore
        user=user, telegram_id=123456789, telegram_username="testuser"
    )


@pytest.fixture
def ai_limits(user):
    """Создание лимитов AI для пользователя"""
    from ai.models import UserAILimits  # type: ignore

    return UserAILimits.objects.create(
        user=user,
        daily_requests=100,
        monthly_requests=3000,
        requests_used_today=0,
        requests_used_this_month=0,
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """Автоматически включает доступ к БД для всех тестов"""
    pass


@pytest.fixture
def mock_fipi_monitor():
    """Мок FIPI монитора"""
    with patch("core.fipi_monitor.FIPIMonitor") as mock_monitor:
        mock_instance = Mock()
        mock_instance.check_updates.return_value = False
        mock_instance.get_new_tasks.return_value = []
        mock_monitor.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def mock_rag_system():
    """Мок RAG системы"""
    with patch("core.rag_system.orchestrator.RAGOrchestrator") as mock_rag:
        mock_instance = Mock()
        mock_instance.process_query.return_value = {
            "context": "Тестовый контекст для AI",
            "sources": [
                {"title": "Задание 1", "content": "Содержание задания 1"},
                {"title": "Задание 2", "content": "Содержание задания 2"},
            ],
            "context_chunks": 2,
        }
        mock_rag.return_value = mock_instance
        yield mock_instance


@pytest.fixture
def selenium_driver():
    """Фикстура для Selenium WebDriver"""
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options

    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=options)
    yield driver
    driver.quit()


@pytest.fixture
def telegram_webhook_data():
    """Тестовые данные Telegram webhook"""
    return {
        "update_id": 123456789,
        "message": {
            "message_id": 1,
            "from": {
                "id": 123456789,
                "is_bot": False,
                "first_name": "Тест",
                "last_name": "Пользователь",
                "username": "testuser",
                "language_code": "ru",
            },
            "chat": {
                "id": 123456789,
                "first_name": "Тест",
                "last_name": "Пользователь",
                "username": "testuser",
                "type": "private",
            },
            "date": 1695123456,
            "text": "/start",
        },
    }


# Маркеры для категоризации тестов
def pytest_configure(config):
    """Конфигурация pytest маркеров"""
    config.addinivalue_line("markers", "unit: mark test as unit test")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "ui: mark test as UI test")
    config.addinivalue_line("markers", "bot: mark test as bot test")
    config.addinivalue_line("markers", "load: mark test as load test")
    config.addinivalue_line("markers", "slow: mark test as slow running")
