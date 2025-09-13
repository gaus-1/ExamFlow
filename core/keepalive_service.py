"""
Улучшенный keepalive сервис для ExamFlow 2.0
Обеспечивает работу 24/7 с учетом ограничений Render бесплатного тарифа
"""

import time
import logging
import requests
import threading
from typing import Dict, Any, Optional
from django.conf import settings
from django.db import connection
from django.core.cache import cache
from django.utils import timezone
import json

logger = logging.getLogger(__name__)

class KeepaliveService:
    """Сервис для поддержания активности всех компонентов"""

    def __init__(self):
        self.website_url = getattr(settings, 'WEBSITE_URL', 'https://examflow.ru')
        self.health_url = "{self.website_url}/health/"
        self.simple_health_url = "{self.website_url}/health/simple/"
        self.bot_token = getattr(settings, 'TELEGRAM_BOT_TOKEN', '')
        self.telegram_api_url = "https://api.telegram.org/bot{self.bot_token}/getMe"

        # Настройки для Render бесплатного тарифа
        self.check_interval = 300  # 5 минут
        self.wake_up_interval = 600  # 10 минут
        self.max_retries = 3
        self.timeout = 30

        # Статистика
        self.stats = {
            'checks_performed': 0,
            'successful_checks': 0,
            'failed_checks': 0,
            'last_check': None,
            'last_success': None,
            'consecutive_failures': 0
        }

        self.is_running = False
        self._thread: Optional[threading.Thread] = None

    def check_website_health(self) -> Dict[str, Any]:
        """Проверяет состояние сайта через health check"""
        try:
            response = requests.get(self.health_url, timeout=self.timeout)

            if response.status_code == 200:
                data = response.json()
                return {
                    'status': 'success',
                    'response_time': response.elapsed.total_seconds(),
                    'health_data': data
                }
            else:
                return {
                    'status': 'error',
                    'error': 'HTTP {response.status_code}',
                    'response_time': response.elapsed.total_seconds()
                }

        except requests.exceptions.Timeout:
            return {
                'status': 'timeout',
                'error': 'Request timeout'
            }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def check_database_connection(self) -> Dict[str, Any]:
        """Проверяет подключение к базе данных"""
        try:
            start_time = time.time()

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()

                if result and result[0] == 1:
                    return {
                        'status': 'success',
                        'response_time': time.time() - start_time
                    }
                else:
                    return {
                        'status': 'error',
                        'error': 'Database query failed'
                    }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def check_telegram_bot(self) -> Dict[str, Any]:
        """Проверяет состояние Telegram бота"""
        try:
            start_time = time.time()

            if not self.bot_token:
                return {
                    'status': 'error',
                    'error': 'Bot token not configured'
                }

            response = requests.get(
                self.telegram_api_url,
                timeout=self.timeout
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return {
                        'status': 'success',
                        'response_time': time.time() - start_time,
                        'bot_info': data.get('result', {})
                    }
                else:
                    return {
                        'status': 'error',
                        'error': data.get('description', 'Unknown error')
                    }
            else:
                return {
                    'status': 'error',
                    'error': 'HTTP {response.status_code}'
                }

        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }

    def wake_up_website(self) -> bool:
        """Будит сайт, делая запросы к различным эндпоинтам"""
        try:
            # Список эндпоинтов для пробуждения
            endpoints = [
                self.website_url,
                "{self.website_url}/",
                self.simple_health_url,
                "{self.website_url}/learning/",
                "{self.website_url}/ai/chat/"
            ]

            success_count = 0

            for endpoint in endpoints:
                try:
                    response = requests.get(endpoint, timeout=15)
                    if response.status_code in [
                            200, 404, 500]:  # Любой ответ лучше чем таймаут
                        success_count += 1
                        logger.info("✅ Пробуждение {endpoint}: {response.status_code}")
                    else:
                        logger.warning("⚠️ {endpoint}: {response.status_code}")

                except Exception as e:
                    logger.warning("❌ {endpoint}: {e}")

            # Считаем успешным, если хотя бы половина эндпоинтов ответила
            success = success_count >= len(endpoints) // 2

            if success:
                logger.info(
                    "✅ Сайт разбужен успешно ({success_count}/{len(endpoints)} эндпоинтов)")
            else:
                logger.warning(
                    "⚠️ Сайт частично разбужен ({success_count}/{len(endpoints)} эндпоинтов)")

            return success

        except Exception as e:
            logger.error("❌ Ошибка пробуждения сайта: {e}")
            return False

    def wake_up_database(self) -> bool:
        """Будит базу данных, выполняя простые запросы"""
        try:
            queries = [
                "SELECT 1",
                "SELECT COUNT(*) FROM core_unifiedprofile",
                "SELECT COUNT(*) FROM learning_subject",
                "SELECT COUNT(*) FROM ai_airequest"
            ]

            success_count = 0

            for query in queries:
                try:
                    with connection.cursor() as cursor:
                        cursor.execute(query)
                        result = cursor.fetchone()
                        if result:
                            success_count += 1
                            logger.info("✅ DB query successful: {query}")
                        else:
                            logger.warning("⚠️ DB query returned no result: {query}")

                except Exception as e:
                    logger.warning("❌ DB query failed: {query} - {e}")

            success = success_count >= len(queries) // 2
            logger.info("База данных: {success_count}/{len(queries)} запросов успешны")

            return success

        except Exception as e:
            logger.error("❌ Ошибка пробуждения базы данных: {e}")
            return False

    def perform_health_check(self) -> Dict[str, Any]:
        """Выполняет полную проверку всех компонентов"""
        self.stats['checks_performed'] += 1
        self.stats['last_check'] = timezone.now()

        results = {
            'timestamp': timezone.now().isoformat(),
            'website': self.check_website_health(),
            'database': self.check_database_connection(),
            'telegram_bot': self.check_telegram_bot()
        }

        # Определяем общий статус
        success_count = sum(
            1 for result in results.values() if isinstance(
                result, dict) and result.get('status') == 'success')
        total_checks = len([r for r in results.values() if isinstance(r, dict)])

        if success_count == total_checks:
            self.stats['successful_checks'] += 1
            self.stats['last_success'] = timezone.now()
            self.stats['consecutive_failures'] = 0
            results['overall_status'] = 'healthy'
        else:
            self.stats['failed_checks'] += 1
            self.stats['consecutive_failures'] += 1
            results['overall_status'] = 'degraded' if success_count > 0 else 'unhealthy'

        results['stats'] = self.stats.copy()

        return results

    def run_keepalive_cycle(self):
        """Основной цикл keepalive"""
        logger.info("🚀 Запуск keepalive цикла")

        while self.is_running:
            try:
                logger.info("🔄 Выполняем проверку компонентов...")

                # Выполняем проверку
                health_results = self.perform_health_check()

                # Логируем результаты
                overall_status = health_results['overall_status']
                logger.info("📊 Статус системы: {overall_status}")

                # Если система нездорова, пытаемся разбудить
                if overall_status != 'healthy':
                    logger.warning(
                        "⚠️ Система нездорова, пытаемся разбудить компоненты...")

                    # Будим сайт
                    if health_results['website'].get('status') != 'success':
                        self.wake_up_website()

                    # Будим базу данных
                    if health_results['database'].get('status') != 'success':
                        self.wake_up_database()

                    # Если много последовательных неудач, отправляем уведомление
                    if self.stats['consecutive_failures'] >= 3:
                        self._send_alert(health_results)

                # Сохраняем статистику в кэш
                cache.set('keepalive_stats', self.stats, 3600)

                # Ждем до следующей проверки
                time.sleep(self.check_interval)

            except Exception as e:
                logger.error("❌ Ошибка в keepalive цикле: {e}")
                time.sleep(60)  # Пауза при ошибке

    def _send_alert(self, health_results: Dict[str, Any]):
        """Отправляет уведомление о проблемах (заглушка)"""
        logger.error(
            "🚨 КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ: {self.stats['consecutive_failures']} последовательных неудач")
        logger.error("📊 Результаты проверки: {json.dumps(health_results, indent=2)}")

        # Здесь можно добавить отправку уведомлений в Telegram
        # или другие системы мониторинга

    def start(self):
        """Запускает keepalive сервис"""
        if self.is_running:
            logger.warning("Keepalive сервис уже запущен")
            return

        self.is_running = True
        self._thread = threading.Thread(target=self.run_keepalive_cycle, daemon=True)
        self._thread.start()
        logger.info("✅ Keepalive сервис запущен")

    def stop(self):
        """Останавливает keepalive сервис"""
        self.is_running = False
        if self._thread:
            self._thread.join(timeout=5)
        logger.info("🛑 Keepalive сервис остановлен")

    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику работы"""
        return {
            'is_running': self.is_running,
            'stats': self.stats.copy(),
            'settings': {
                'check_interval': self.check_interval,
                'wake_up_interval': self.wake_up_interval,
                'max_retries': self.max_retries,
                'timeout': self.timeout
            }
        }

# Глобальный экземпляр сервиса
keepalive_service = KeepaliveService()
