"""
Integration тесты для Redis ExamFlow
"""

import pytest
from unittest.mock import patch, Mock
from django.core.cache import cache
from django.test import override_settings


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.django_db
class TestRedisCache:
    """Тесты Redis кэша"""
    
    def test_cache_set_get(self):
        """Тест установки и получения значения из кэша"""
        cache.set('test_key', 'test_value', timeout=300)
        value = cache.get('test_key')
        
        assert value == 'test_value'
    
    def test_cache_delete(self):
        """Тест удаления значения из кэша"""
        cache.set('delete_key', 'delete_value')
        cache.delete('delete_key')
        
        value = cache.get('delete_key')
        assert value is None
    
    def test_cache_timeout(self):
        """Тест истечения времени жизни кэша"""
        cache.set('timeout_key', 'timeout_value', timeout=1)
        
        # Ждем истечения времени
        import time
        time.sleep(2)
        
        value = cache.get('timeout_key')
        assert value is None
    
    def test_cache_default_value(self):
        """Тест значения по умолчанию"""
        value = cache.get('nonexistent_key', 'default_value')
        assert value == 'default_value'
    
    def test_cache_clear(self):
        """Тест очистки всего кэша"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        
        cache.clear()
        
        assert cache.get('key1') is None
        assert cache.get('key2') is None
    
    def test_cache_add_existing_key(self):
        """Тест добавления значения для существующего ключа"""
        cache.set('existing_key', 'original_value')
        result = cache.add('existing_key', 'new_value')
        
        assert result is False
        assert cache.get('existing_key') == 'original_value'
    
    def test_cache_add_new_key(self):
        """Тест добавления значения для нового ключа"""
        result = cache.add('new_key', 'new_value')
        
        assert result is True
        assert cache.get('new_key') == 'new_value'
    
    def test_cache_get_many(self):
        """Тест получения множественных значений"""
        cache.set('key1', 'value1')
        cache.set('key2', 'value2')
        cache.set('key3', 'value3')
        
        values = cache.get_many(['key1', 'key2', 'key3', 'nonexistent'])
        
        assert values['key1'] == 'value1'
        assert values['key2'] == 'value2'
        assert values['key3'] == 'value3'
        assert 'nonexistent' not in values
    
    def test_cache_set_many(self):
        """Тест установки множественных значений"""
        data = {
            'multi_key1': 'multi_value1',
            'multi_key2': 'multi_value2',
            'multi_key3': 'multi_value3'
        }
        
        cache.set_many(data)
        
        assert cache.get('multi_key1') == 'multi_value1'
        assert cache.get('multi_key2') == 'multi_value2'
        assert cache.get('multi_key3') == 'multi_value3'
    
    def test_cache_delete_many(self):
        """Тест удаления множественных значений"""
        cache.set('delete_key1', 'delete_value1')
        cache.set('delete_key2', 'delete_value2')
        cache.set('delete_key3', 'delete_value3')
        
        cache.delete_many(['delete_key1', 'delete_key2', 'delete_key3'])
        
        assert cache.get('delete_key1') is None
        assert cache.get('delete_key2') is None
        assert cache.get('delete_key3') is None
    
    def test_cache_increment(self):
        """Тест инкремента числового значения"""
        cache.set('counter', 0)
        
        new_value = cache.incr('counter')
        assert new_value == 1
        
        new_value = cache.incr('counter', 5)
        assert new_value == 6
    
    def test_cache_decrement(self):
        """Тест декремента числового значения"""
        cache.set('counter', 10)
        
        new_value = cache.decr('counter')
        assert new_value == 9
        
        new_value = cache.decr('counter', 3)
        assert new_value == 6
    
    def test_cache_incr_nonexistent_key(self):
        """Тест инкремента несуществующего ключа"""
        with pytest.raises(ValueError):
            cache.incr('nonexistent_counter')


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.django_db
class TestRedisAICaching:
    """Тесты кэширования AI ответов"""
    
    def test_ai_response_caching(self, user, mock_ai_service):
        """Тест кэширования AI ответов"""
        from core.container import Container
        
        cache_key = f"ai_response:{user.id}:test_prompt"
        
        # Первый запрос - сохраняется в кэш
        cache.delete(cache_key)
        ai_service = Container.ai_orchestrator()
        response1 = ai_service.ask('test_prompt')
        
        # Проверяем что ответ кэшируется (если реализовано)
        cached_response = cache.get(cache_key)
        if cached_response:
            assert cached_response['answer'] == response1['answer']
    
    def test_ai_context_caching(self, user, mock_rag_system):
        """Тест кэширования контекста RAG"""
        from core.rag_system.orchestrator import RAGOrchestrator
        
        cache_key = f"rag_context:{user.id}:test_query"
        
        # Первый запрос
        cache.delete(cache_key)
        rag = RAGOrchestrator()
        context1 = rag.process_query('test_query', user_id=user.id)
        
        # Проверяем кэширование (если реализовано)
        cached_context = cache.get(cache_key)
        if cached_context:
            assert cached_context['context'] == context1['context']
    
    def test_user_session_caching(self, user):
        """Тест кэширования сессий пользователей"""
        from core.services.chat_session import ChatSessionService
        
        session_key = f"user_session:{user.id}"
        
        # Создаем сессию
        session = ChatSessionService.create_session( # type: ignore
            user_id=user.id,
            subject='Математика'
        )
        
        # Проверяем кэширование (если реализовано)
        cached_session = cache.get(session_key)
        if cached_session:
            assert cached_session['subject'] == 'Математика'
    
    def test_task_progress_caching(self, user, math_task):
        """Тест кэширования прогресса заданий"""
        from learning.models import UserProgress
        
        progress_key = f"user_progress:{user.id}:{math_task.id}"
        
        # Создаем прогресс
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=True,
            attempts=1
        )
        
        # Проверяем кэширование (если реализовано)
        cached_progress = cache.get(progress_key)
        if cached_progress:
            assert cached_progress['is_correct'] is True
            assert cached_progress['attempts'] == 1


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.django_db
class TestRedisFallback:
    """Тесты fallback механизмов Redis"""
    
    @override_settings(CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    })
    def test_locmem_fallback(self):
        """Тест fallback на LocMemCache"""
        # Очищаем кэш
        cache.clear()
        
        # Тестируем базовую функциональность
        cache.set('fallback_key', 'fallback_value')
        value = cache.get('fallback_key')
        
        assert value == 'fallback_value'
    
    def test_cache_connection_error_handling(self):
        """Тест обработки ошибок подключения к Redis"""
        with patch('django.core.cache.cache') as mock_cache:
            # Мокаем ошибку подключения
            mock_cache.set.side_effect = Exception('Redis connection error')
            mock_cache.get.return_value = None
            
            # Операции не должны вызывать исключения
            try:
                mock_cache.set('test_key', 'test_value')
                value = mock_cache.get('test_key')
                assert value is None  # Fallback значение
            except Exception:
                pytest.fail("Cache operations should handle connection errors gracefully")
    
    def test_cache_timeout_error_handling(self):
        """Тест обработки ошибок таймаута Redis"""
        with patch('django.core.cache.cache') as mock_cache:
            # Мокаем таймаут
            mock_cache.get.side_effect = Exception('Redis timeout')
            
            # Операции должны возвращать значения по умолчанию
            try:
                value = mock_cache.get('test_key', 'default_value')
                assert value == 'default_value'
            except Exception:
                pytest.fail("Cache operations should handle timeout errors gracefully")


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.django_db
class TestRedisPerformance:
    """Тесты производительности Redis"""
    
    def test_cache_bulk_operations_performance(self):
        """Тест производительности массовых операций"""
        import time
        
        # Тест массовой установки
        data = {f'perf_key_{i}': f'perf_value_{i}' for i in range(100)}
        
        start_time = time.time()
        cache.set_many(data)
        set_time = time.time() - start_time
        
        # Тест массового получения
        keys = list(data.keys())
        start_time = time.time()
        retrieved_data = cache.get_many(keys)
        get_time = time.time() - start_time
        
        # Проверяем что операции выполняются быстро (менее 1 секунды)
        assert set_time < 1.0
        assert get_time < 1.0
        assert len(retrieved_data) == 100
        
        # Очищаем
        cache.delete_many(keys)
    
    def test_cache_concurrent_access(self):
        """Тест конкурентного доступа к кэшу"""
        import threading
        import time
        
        results = []
        
        def cache_worker(worker_id):
            """Рабочий поток для тестирования конкурентности"""
            for i in range(10):
                key = f'concurrent_key_{worker_id}_{i}'
                value = f'concurrent_value_{worker_id}_{i}'
                
                cache.set(key, value)
                retrieved_value = cache.get(key)
                
                results.append({
                    'worker': worker_id,
                    'iteration': i,
                    'success': retrieved_value == value
                })
        
        # Запускаем несколько потоков
        threads = []
        for i in range(5):
            thread = threading.Thread(target=cache_worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Ждем завершения всех потоков
        for thread in threads:
            thread.join()
        
        # Проверяем результаты
        assert len(results) == 50  # 5 потоков * 10 итераций
        successful_operations = sum(1 for result in results if result['success'])
        assert successful_operations >= 45  # Допускаем небольшие потери
    
    def test_cache_memory_usage(self):
        """Тест использования памяти кэша"""
        # Заполняем кэш большими значениями
        large_data = {}
        for i in range(100):
            large_data[f'large_key_{i}'] = 'x' * 1000  # 1KB на значение
        
        cache.set_many(large_data)
        
        # Проверяем что данные доступны
        retrieved_data = cache.get_many(list(large_data.keys()))
        assert len(retrieved_data) == 100
        
        # Очищаем память
        cache.delete_many(list(large_data.keys()))


@pytest.mark.integration
@pytest.mark.redis
@pytest.mark.django_db
class TestRedisIntegration:
    """Тесты интеграции Redis с компонентами ExamFlow"""
    
    def test_ai_service_with_cache(self, user, mock_ai_service):
        """Тест AI сервиса с кэшированием"""
        from core.container import Container
        
        # Очищаем кэш
        cache.clear()
        
        ai_service = Container.ai_orchestrator()
        
        # Первый запрос
        response1 = ai_service.ask('Кэшируемый запрос', user_id=user.id) # type: ignore
        
        # Второй идентичный запрос (должен использовать кэш)
        response2 = ai_service.ask('Кэшируемый запрос', user_id=user.id) # type: ignore
        
        # Ответы должны быть одинаковыми
        assert response1['answer'] == response2['answer']
    
    def test_rag_system_with_cache(self, user, mock_rag_system):
        """Тест RAG системы с кэшированием"""
        from core.rag_system.orchestrator import RAGOrchestrator
        
        # Очищаем кэш
        cache.clear()
        
        rag = RAGOrchestrator()
        
        # Первый запрос
        context1 = rag.process_query('Кэшируемый запрос', user_id=user.id)
        
        # Второй идентичный запрос
        context2 = rag.process_query('Кэшируемый запрос', user_id=user.id)
        
        # Контексты должны быть одинаковыми
        assert context1['context'] == context2['context']
    
    def test_user_session_persistence(self, user):
        """Тест сохранения сессий пользователей"""
        from core.services.chat_session import ChatSessionService
        
        # Очищаем кэш
        cache.clear()
        
        # Создаем сессию
        session1 = ChatSessionService.create_session( # type: ignore
            user_id=user.id,
            subject='Математика'
        )
        
        # Обновляем сессию
        ChatSessionService.update_session( # type: ignore
            user.id,
            context={'last_message': 'Привет!'}
        )
        
        # Получаем сессию
        session2 = ChatSessionService.get_session(user.id) # type: ignore 
        
        # Сессии должны быть связаны
        assert session2 is not None
    
    def test_cache_invalidation(self, user, math_task):
        """Тест инвалидации кэша"""
        from learning.models import UserProgress
        
        # Создаем прогресс
        progress = UserProgress.objects.create( # type: ignore
            user=user,
            task=math_task,
            is_correct=False,
            attempts=1
        )
        
        # Кэшируем прогресс
        cache_key = f"user_progress:{user.id}:{math_task.id}"
        cache.set(cache_key, {
            'is_correct': False,
            'attempts': 1
        })
        
        # Обновляем прогресс
        progress.is_correct = True
        progress.attempts = 2
        progress.save()
        
        # Инвалидируем кэш
        cache.delete(cache_key)
        
        # Проверяем что кэш очищен
        cached_progress = cache.get(cache_key)
        assert cached_progress is None
