"""
Расширенный health check для ExamFlow 2.0
Проверяет все компоненты системы и возвращает детальную информацию о состоянии
"""

import time
import logging
from typing import Dict, Any, Optional
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
import requests
import os

# Попытка импорта psutil (может отсутствовать на некоторых системах)
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

logger = logging.getLogger(__name__)


class SystemHealthChecker:
    """Проверка состояния всех компонентов системы"""
    
    def __init__(self):
        self.start_time = time.time()
        self.checks = {}
    
    def check_database(self) -> Dict[str, Any]:
        """Проверяет состояние базы данных"""
        try:
            start_time = time.time()
            
            with connection.cursor() as cursor:
                # Проверяем подключение
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                if not result or result[0] != 1:
                    return {
                        'status': 'unhealthy',
                        'error': 'Database query failed',
                        'response_time': time.time() - start_time
                    }
                
                # Проверяем основные таблицы
                cursor.execute("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public' 
                    AND table_name IN ('core_unifiedprofile', 'learning_subject', 'ai_airequest')
                """)
                table_count = cursor.fetchone()[0]
                
                if table_count < 3:
                    return {
                        'status': 'degraded',
                        'warning': 'Some required tables missing',
                        'response_time': time.time() - start_time
                    }
                
                return {
                    'status': 'healthy',
                    'response_time': time.time() - start_time,
                    'tables_checked': table_count
                }
                
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def check_telegram_bot(self) -> Dict[str, Any]:
        """Проверяет состояние Telegram бота"""
        try:
            start_time = time.time()
            
            token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
            if not token:
                return {
                    'status': 'unhealthy',
                    'error': 'TELEGRAM_BOT_TOKEN not configured',
                    'response_time': time.time() - start_time
                }
            
            # Проверяем API бота
            response = requests.get(
                f"https://api.telegram.org/bot{token}/getMe",
                timeout=10
            )
            
            if response.status_code != 200:
                return {
                    'status': 'unhealthy',
                    'error': f'Telegram API returned {response.status_code}',
                    'response_time': time.time() - start_time
                }
            
            data = response.json()
            if not data.get('ok'):
                return {
                    'status': 'unhealthy',
                    'error': data.get('description', 'Unknown error'),
                    'response_time': time.time() - start_time
                }
            
            return {
                'status': 'healthy',
                'response_time': time.time() - start_time,
                'bot_info': {
                    'username': data.get('result', {}).get('username'),
                    'first_name': data.get('result', {}).get('first_name')
                }
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'error': str(e),
                'response_time': time.time() - start_time
            }
    
    def check_ai_services(self) -> Dict[str, Any]:
        """Проверяет состояние ИИ сервисов"""
        try:
            start_time = time.time()
            
            # Проверяем Gemini API
            gemini_key = getattr(settings, 'GEMINI_API_KEY', None)
            if not gemini_key:
                return {
                    'status': 'degraded',
                    'warning': 'GEMINI_API_KEY not configured',
                    'response_time': time.time() - start_time
                }
            
            # Проверяем доступность Gemini API
            response = requests.post(
                "https://generativelanguage.googleapis.com/v1beta/models",
                headers={'Authorization': f'Bearer {gemini_key}'},
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'status': 'healthy',
                    'response_time': time.time() - start_time,
                    'ai_provider': 'gemini'
                }
            else:
                return {
                    'status': 'degraded',
                    'warning': f'Gemini API returned {response.status_code}',
                    'response_time': time.time() - start_time
                }
                
        except Exception as e:
            return {
                'status': 'degraded',
                'warning': str(e),
                'response_time': time.time() - start_time
            }
    
    def check_memory_usage(self) -> Dict[str, Any]:
        """Проверяет использование памяти"""
        if not PSUTIL_AVAILABLE:
            return {
                'status': 'healthy',
                'memory_usage_mb': 0,
                'warning': 'Memory monitoring not available (psutil not installed)'
            }
        
        try:
            process = psutil.Process(os.getpid())
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            # Для Render бесплатного тарифа лимит ~512MB
            if memory_mb > 400:
                return {
                    'status': 'warning',
                    'memory_usage_mb': round(memory_mb, 2),
                    'warning': 'High memory usage'
                }
            elif memory_mb > 300:
                return {
                    'status': 'degraded',
                    'memory_usage_mb': round(memory_mb, 2),
                    'warning': 'Memory usage approaching limit'
                }
            else:
                return {
                    'status': 'healthy',
                    'memory_usage_mb': round(memory_mb, 2)
                }
                
        except Exception as e:
            return {
                'status': 'degraded',
                'warning': f'Could not check memory: {str(e)}'
            }
    
    def check_cache(self) -> Dict[str, Any]:
        """Проверяет состояние кэша"""
        try:
            start_time = time.time()
            
            # Тестируем запись и чтение из кэша
            test_key = 'health_check_test'
            test_value = f'test_{int(time.time())}'
            
            cache.set(test_key, test_value, 60)
            cached_value = cache.get(test_key)
            
            if cached_value != test_value:
                return {
                    'status': 'degraded',
                    'warning': 'Cache read/write test failed',
                    'response_time': time.time() - start_time
                }
            
            cache.delete(test_key)
            
            return {
                'status': 'healthy',
                'response_time': time.time() - start_time
            }
            
        except Exception as e:
            return {
                'status': 'degraded',
                'warning': str(e),
                'response_time': time.time() - start_time
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """Возвращает информацию о системе"""
        try:
            info = {
                'uptime_seconds': time.time() - self.start_time,
                'python_version': os.sys.version, # type: ignore
                'django_version': getattr(settings, 'DJANGO_VERSION', 'Unknown'),
                'debug_mode': settings.DEBUG,
                'environment': os.getenv('ENVIRONMENT', 'production')
            }
            
            if PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process(os.getpid())
                    info.update({
                        'memory_usage_mb': round(process.memory_info().rss / 1024 / 1024, 2),
                        'cpu_percent': process.cpu_percent()
                    })
                except Exception:
                    info['memory_usage_mb'] = 0
                    info['cpu_percent'] = 0
            else:
                info['memory_usage_mb'] = 0
                info['cpu_percent'] = 0
                info['psutil_available'] = False
            
            return info
        except Exception as e:
            return {
                'error': f'Could not get system info: {str(e)}'
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """Запускает все проверки и возвращает общий статус"""
        start_time = time.time()
        
        # Выполняем все проверки
        self.checks = {
            'database': self.check_database(),
            'telegram_bot': self.check_telegram_bot(),
            'ai_services': self.check_ai_services(),
            'memory': self.check_memory_usage(),
            'cache': self.check_cache()
        }
        
        # Определяем общий статус
        unhealthy_count = sum(1 for check in self.checks.values() 
                            if check.get('status') == 'unhealthy')
        warning_count = sum(1 for check in self.checks.values() 
                          if check.get('status') == 'warning')
        degraded_count = sum(1 for check in self.checks.values() 
                           if check.get('status') == 'degraded')
        
        if unhealthy_count > 0:
            overall_status = 'unhealthy'
        elif degraded_count > 0 or warning_count > 0:
            overall_status = 'degraded'
        else:
            overall_status = 'healthy'
        
        return {
            'status': overall_status,
            'timestamp': timezone.now().isoformat(),
            'response_time': time.time() - start_time,
            'checks': self.checks,
            'system_info': self.get_system_info(),
            'summary': {
                'total_checks': len(self.checks),
                'healthy': sum(1 for check in self.checks.values() 
                              if check.get('status') == 'healthy'),
                'degraded': degraded_count,
                'warning': warning_count,
                'unhealthy': unhealthy_count
            }
        }


def health_check_view(request):
    """Health check endpoint для Render и мониторинга"""
    try:
        checker = SystemHealthChecker()
        health_data = checker.run_all_checks()
        
        # Определяем HTTP статус код
        if health_data['status'] == 'unhealthy':
            status_code = 503
        elif health_data['status'] == 'degraded':
            status_code = 200  # 200, но с предупреждениями
        else:
            status_code = 200
        
        return JsonResponse(health_data, status=status_code)
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': timezone.now().isoformat()
        }, status=500)


def simple_health_check(request):
    """Простой health check для быстрых проверок"""
    try:
        # Быстрая проверка базы данных
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            
        if result and result[0] == 1:
            return JsonResponse({
                'status': 'healthy',
                'timestamp': timezone.now().isoformat()
            })
        else:
            return JsonResponse({
                'status': 'unhealthy',
                'error': 'Database check failed'
            }, status=503)
            
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=503)
