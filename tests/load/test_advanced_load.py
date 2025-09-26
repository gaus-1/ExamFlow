"""
Продвинутые нагрузочные тесты
"""

import json
import logging
import random
import time

import pytest
from locust import HttpUser, between, task
from locust.env import Environment
from locust.log import setup_logging

logger = logging.getLogger(__name__)


class ExamFlowUser(HttpUser):
    """Пользователь ExamFlow для нагрузочного тестирования"""

    wait_time = between(1, 3)

    def on_start(self):
        """Инициализация пользователя"""
        self.user_id = random.randint(100000, 999999)
        self.subjects = ["математика", "русский язык"]
        self.current_subject = random.choice(self.subjects)

        logger.info(f"User {self.user_id} started with subject {self.current_subject}")

    @task(3)
    def visit_homepage(self):
        """Посещение главной страницы"""
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage returned {response.status_code}")

    @task(2)
    def visit_subjects(self):
        """Посещение страницы предметов"""
        with self.client.get("/subjects/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Subjects page returned {response.status_code}")

    @task(1)
    def ai_query(self):
        """Запрос к AI"""
        prompts = [
            "Реши уравнение x + 2 = 5",
            "Объясни тему функций",
            "Как решать квадратные уравнения?",
            "Помоги с задачей по геометрии",
            "Что такое производная?",
        ]

        prompt = random.choice(prompts)

        data = {
            "prompt": prompt,
            "subject": self.current_subject,
            "user_id": self.user_id,
        }

        with self.client.post(
            "/api/ai/ask/", json=data, catch_response=True
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "answer" in result:
                        response.success()
                    else:
                        response.failure("No answer in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"AI query returned {response.status_code}")

    @task(1)
    def search_tasks(self):
        """Поиск заданий"""
        search_queries = [
            "уравнения",
            "функции",
            "геометрия",
            "алгебра",
            "тригонометрия",
            "сочинение",
            "орфография",
            "пунктуация",
        ]

        query = random.choice(search_queries)

        with self.client.get(
            f"/api/fipi/search/?q={query}&subject={self.current_subject}",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "results" in result:
                        response.success()
                    else:
                        response.failure("No results in response")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"Search returned {response.status_code}")

    @task(1)
    def health_check(self):
        """Проверка здоровья системы"""
        with self.client.get("/api/health/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Health check returned {response.status_code}")

    @task(1)
    def faq_page(self):
        """Посещение FAQ"""
        with self.client.get("/faq/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"FAQ page returned {response.status_code}")


class ExamFlowAPIUser(HttpUser):
    """API пользователь для нагрузочного тестирования"""

    wait_time = between(0.5, 1.5)

    def on_start(self):
        """Инициализация API пользователя"""
        self.api_key = f"test_key_{random.randint(1000, 9999)}"
        self.user_id = random.randint(100000, 999999)

    @task(5)
    def ai_query_heavy(self):
        """Тяжелые AI запросы"""
        complex_prompts = [
            "Реши систему уравнений: x + y = 5, 2x - y = 1",
            "Найди производную функции f(x) = x^3 + 2x^2 - 5x + 1",
            "Построй график функции y = sin(x) на промежутке [0, 2π]",
            "Напиши сочинение на тему 'Роль образования в современном обществе'",
            "Разбери синтаксическую структуру предложения: 'Быстро бежал по лесу молодой олень.'",
        ]

        prompt = random.choice(complex_prompts)

        data = {
            "prompt": prompt,
            "subject": random.choice(["математика", "русский язык"]),
            "user_id": self.user_id,
            "use_context": True,
        }

        with self.client.post(
            "/api/ai/ask/",
            json=data,
            headers={"Authorization": f"Bearer {self.api_key}"},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                try:
                    result = response.json()
                    if "answer" in result and len(result["answer"]) > 10:
                        response.success()
                    else:
                        response.failure("Insufficient answer length")
                except json.JSONDecodeError:
                    response.failure("Invalid JSON response")
            else:
                response.failure(f"AI query returned {response.status_code}")

    @task(3)
    def batch_search(self):
        """Пакетный поиск"""
        queries = ["математика", "русский", "егэ", "огэ", "задания"]

        for query in queries:
            with self.client.get(
                f"/api/fipi/search/?q={query}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                catch_response=True,
            ) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure(f"Batch search returned {response.status_code}")

    @task(2)
    def get_statistics(self):
        """Получение статистики"""
        endpoints = ["/api/ai/stats/", "/api/vector/stats/", "/api/health/"]

        endpoint = random.choice(endpoints)

        with self.client.get(
            endpoint,
            headers={"Authorization": f"Bearer {self.api_key}"},
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Statistics endpoint returned {response.status_code}")

    @task(1)
    def concurrent_requests(self):
        """Конкурентные запросы"""
        import concurrent.futures

        def make_request():
            data = {
                "prompt": f"Запрос {random.randint(1, 100)}",
                "subject": "математика",
                "user_id": self.user_id,
            }

            response = self.client.post(
                "/api/ai/ask/",
                json=data,
                headers={"Authorization": f"Bearer {self.api_key}"},
            )
            return response.status_code == 200

        # Делаем 5 одновременных запросов
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(5)]
            results = [future.result() for future in futures]

            success_rate = sum(results) / len(results)
            if success_rate >= 0.8:  # 80% успешных запросов
                self.environment.events.request.fire(
                    request_type="POST",
                    name="concurrent_requests",
                    response_time=0,
                    response_length=0,
                )
            else:
                logger.warning(
                    f"Low success rate in concurrent requests: {success_rate}"
                )


@pytest.mark.load
@pytest.mark.slow
class TestAdvancedLoadTesting:
    """Продвинутые нагрузочные тесты"""

    def test_sustained_load(self):
        """Тест продолжительной нагрузки"""
        logger.info("Starting sustained load test")

        # Создаем окружение Locust
        env = Environment(user_classes=[ExamFlowUser])
        env.create_local_runner()

        # Настраиваем логирование
        setup_logging("INFO", None)

        # Запускаем тест на 2 минуты
        env.runner.start(10, spawn_rate=2)  # 10 пользователей, 2 в секунду

        # Ждем 2 минуты
        time.sleep(120)

        # Останавливаем тест
        env.runner.quit()

        # Получаем статистику
        stats = env.stats

        logger.info("Sustained Load Test Results:")
        logger.info(f"Total requests: {stats.total.num_requests}")
        logger.info(f"Success rate: {stats.total.get_response_time_percentile(0.5)}%")

        # Проверяем, что успешность запросов выше 95%
        success_rate = (
            (stats.total.num_requests - stats.total.num_failures)
            / stats.total.num_requests
            * 100
        )
        assert success_rate >= 95.0, f"Success rate too low: {success_rate}%"

    def test_peak_load(self):
        """Тест пиковой нагрузки"""
        logger.info("Starting peak load test")

        env = Environment(user_classes=[ExamFlowUser, ExamFlowAPIUser])
        env.create_local_runner()

        # Быстро увеличиваем нагрузку до пика
        env.runner.start(50, spawn_rate=10)  # 50 пользователей, 10 в секунду

        # Держим пиковую нагрузку 1 минуту
        time.sleep(60)

        env.runner.quit()

        stats = env.stats
        success_rate = (
            (stats.total.num_requests - stats.total.num_failures)
            / stats.total.num_requests
            * 100
        )

        logger.info(f"Peak Load Test - Success rate: {success_rate}%")

        # При пиковой нагрузке допускаем 90% успешности
        assert success_rate >= 90.0, f"Peak load success rate too low: {success_rate}%"

    def test_stress_test(self):
        """Стресс-тест"""
        logger.info("Starting stress test")

        env = Environment(user_classes=[ExamFlowAPIUser])
        env.create_local_runner()

        # Постепенно увеличиваем нагрузку до предела
        for users in [10, 25, 50, 75, 100]:
            logger.info(f"Testing with {users} users")
            env.runner.start(users, spawn_rate=5)
            time.sleep(30)  # Тестируем 30 секунд на каждом уровне

        env.runner.quit()

        stats = env.stats
        success_rate = (
            (stats.total.num_requests - stats.total.num_failures)
            / stats.total.num_requests
            * 100
        )

        logger.info(f"Stress Test - Success rate: {success_rate}%")

        # При стресс-тесте допускаем 85% успешности
        assert (
            success_rate >= 85.0
        ), f"Stress test success rate too low: {success_rate}%"

    def test_spike_test(self):
        """Тест на всплески нагрузки"""
        logger.info("Starting spike test")

        env = Environment(user_classes=[ExamFlowUser])
        env.create_local_runner()

        # Базовая нагрузка
        env.runner.start(10, spawn_rate=2)
        time.sleep(30)

        # Всплеск нагрузки
        env.runner.start(100, spawn_rate=20)  # Резкий всплеск
        time.sleep(60)

        # Возврат к базовой нагрузке
        env.runner.start(10, spawn_rate=2)
        time.sleep(30)

        env.runner.quit()

        stats = env.stats
        success_rate = (
            (stats.total.num_requests - stats.total.num_failures)
            / stats.total.num_requests
            * 100
        )

        logger.info(f"Spike Test - Success rate: {success_rate}%")

        # Система должна восстановиться после всплеска
        assert success_rate >= 90.0, f"Spike test success rate too low: {success_rate}%"

    def test_endurance_test(self):
        """Тест на выносливость (длительная нагрузка)"""
        logger.info("Starting endurance test")

        env = Environment(user_classes=[ExamFlowUser])
        env.create_local_runner()

        # Средняя нагрузка в течение 5 минут
        env.runner.start(20, spawn_rate=3)
        time.sleep(300)  # 5 минут

        env.runner.quit()

        stats = env.stats

        # Проверяем, что нет деградации производительности
        avg_response_time = stats.total.avg_response_time
        max_response_time = stats.total.max_response_time

        logger.info(f"Endurance Test - Avg response time: {avg_response_time}ms")
        logger.info(f"Endurance Test - Max response time: {max_response_time}ms")

        # Средний время ответа должно быть разумным
        assert (
            avg_response_time < 5000
        ), f"Average response time too high: {avg_response_time}ms"

        # Максимальное время ответа не должно превышать 30 секунд
        assert (
            max_response_time < 30000
        ), f"Max response time too high: {max_response_time}ms"

    def test_memory_leak_detection(self):
        """Тест на утечки памяти"""
        logger.info("Starting memory leak detection test")

        import os

        import psutil

        # Получаем начальное потребление памяти
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        env = Environment(user_classes=[ExamFlowUser])
        env.create_local_runner()

        # Запускаем тест с циклической нагрузкой
        for cycle in range(5):
            logger.info(f"Memory test cycle {cycle + 1}/5")

            env.runner.start(15, spawn_rate=3)
            time.sleep(60)  # 1 минута нагрузки
            env.runner.stop()
            time.sleep(10)  # Пауза между циклами

            # Проверяем потребление памяти
            current_memory = process.memory_info().rss / 1024 / 1024
            memory_increase = current_memory - initial_memory

            logger.info(
                f"Memory increase after cycle {cycle + 1}: {memory_increase:.2f}MB"
            )

            # Потребление памяти не должно расти критически
            assert (
                memory_increase < 100
            ), f"Memory leak detected: {memory_increase:.2f}MB increase"

        env.runner.quit()

        final_memory = process.memory_info().rss / 1024 / 1024
        total_memory_increase = final_memory - initial_memory

        logger.info(f"Total memory increase: {total_memory_increase:.2f}MB")

        # Общий рост памяти не должен превышать 50MB
        assert (
            total_memory_increase < 50
        ), f"Significant memory leak: {total_memory_increase:.2f}MB"

    def test_concurrent_users_scalability(self):
        """Тест масштабируемости по количеству пользователей"""
        logger.info("Starting scalability test")

        results = []

        for user_count in [5, 10, 20, 30, 40, 50]:
            logger.info(f"Testing with {user_count} concurrent users")

            env = Environment(user_classes=[ExamFlowUser])
            env.create_local_runner()

            env.runner.start(user_count, spawn_rate=5)
            time.sleep(60)  # Тестируем 1 минуту

            stats = env.stats
            success_rate = (
                (stats.total.num_requests - stats.total.num_failures)
                / stats.total.num_requests
                * 100
            )
            avg_response_time = stats.total.avg_response_time

            results.append(
                {
                    "users": user_count,
                    "success_rate": success_rate,
                    "avg_response_time": avg_response_time,
                    "requests_per_second": stats.total.num_requests / 60,
                }
            )

            env.runner.quit()
            time.sleep(10)  # Пауза между тестами

        # Анализируем результаты
        logger.info("Scalability Test Results:")
        for result in results:
            logger.info(
                f"Users: {result['users']}, "
                f"Success: {result['success_rate']:.1f}%, "
                f"Avg Time: {result['avg_response_time']:.0f}ms, "
                f"RPS: {result['requests_per_second']:.1f}"
            )

        # Проверяем, что система масштабируется линейно
        # Успешность не должна падать критически
        min_success_rate = min(r["success_rate"] for r in results)
        assert (
            min_success_rate >= 85.0
        ), f"Scalability degraded: min success rate {min_success_rate}%"

        # Время ответа не должно расти экспоненциально
        response_times = [r["avg_response_time"] for r in results]
        max_response_time = max(response_times)
        assert (
            max_response_time < 10000
        ), f"Response time degraded: max {max_response_time}ms"
