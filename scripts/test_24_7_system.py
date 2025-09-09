#!/usr/bin/env python3
"""
Скрипт для тестирования системы 24/7 ExamFlow 2.0
"""

import requests
import time
import json
from typing import Dict, Any, List
from datetime import datetime

class SystemTester:
    """Тестирование системы ExamFlow 2.0"""
    
    def __init__(self, base_url: str = "https://examflow.ru"):
        self.base_url = base_url
        self.results = []
        self.start_time = time.time()
    
    def test_endpoint(self, name: str, url: str, expected_status: int = 200, timeout: int = 30) -> Dict[str, Any]:
        """Тестирует эндпоинт"""
        try:
            start_time = time.time()
            response = requests.get(url, timeout=timeout)
            response_time = time.time() - start_time
            
            result = {
                'name': name,
                'url': url,
                'status_code': response.status_code,
                'response_time': response_time,
                'success': response.status_code == expected_status,
                'timestamp': datetime.now().isoformat()
            }
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    result['data'] = data
                except Exception:
                    result['data'] = response.text[:200]
            
            self.results.append(result)
            return result
            
        except requests.exceptions.Timeout:
            result = {
                'name': name,
                'url': url,
                'status_code': 0,
                'response_time': timeout,
                'success': False,
                'error': 'Timeout',
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
            
        except Exception as e:
            result = {
                'name': name,
                'url': url,
                'status_code': 0,
                'response_time': 0,
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.results.append(result)
            return result
    
    def test_all_endpoints(self) -> List[Dict[str, Any]]:
        """Тестирует все основные эндпоинты"""
        print("🧪 Тестирование системы ExamFlow 2.0...")
        print("=" * 50)
        
        endpoints = [
            ("Главная страница", f"{self.base_url}/"),
            ("Health Check", f"{self.base_url}/health/"),
            ("Simple Health Check", f"{self.base_url}/health/simple/"),
            ("Features", f"{self.base_url}/features/"),
            ("Pricing", f"{self.base_url}/pricing/"),
            ("Subjects", f"{self.base_url}/learning/subjects/"),
            ("AI Chat", f"{self.base_url}/ai/chat/"),
            ("Telegram Bot Webhook", f"{self.base_url}/bot/webhook/"),
            ("Bot API Status", f"{self.base_url}/bot/api/status/"),
            ("API Subjects", f"{self.base_url}/api/subjects/"),
            ("API Tasks", f"{self.base_url}/api/tasks/random/"),
            ("API Health", f"{self.base_url}/api/health/"),
        ]
        
        for name, url in endpoints:
            print(f"🔍 Тестируем {name}...")
            result = self.test_endpoint(name, url)
            
            if result['success']:
                print(f"   ✅ {name}: {result['status_code']} ({result['response_time']:.2f}s)")
            else:
                print(f"   ❌ {name}: {result.get('error', result['status_code'])}")
        
        return self.results
    
    def test_performance(self) -> Dict[str, Any]:
        """Тестирует производительность системы"""
        print("\n⚡ Тестирование производительности...")
        
        # Тестируем главную страницу несколько раз
        response_times = []
        for i in range(5):
            result = self.test_endpoint(f"Performance Test {i+1}", f"{self.base_url}/")
            response_times.append(result['response_time'])
            time.sleep(1)
        
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)
        min_response_time = min(response_times)
        
        performance = {
            'average_response_time': avg_response_time,
            'max_response_time': max_response_time,
            'min_response_time': min_response_time,
            'response_times': response_times,
            'performance_grade': self._get_performance_grade(avg_response_time)
        }
        
        print(f"   📊 Среднее время ответа: {avg_response_time:.2f}s")
        print(f"   📊 Максимальное время: {max_response_time:.2f}s")
        print(f"   📊 Минимальное время: {min_response_time:.2f}s")
        print(f"   📊 Оценка производительности: {performance['performance_grade']}")
        
        return performance
    
    def _get_performance_grade(self, response_time: float) -> str:
        """Определяет оценку производительности"""
        if response_time < 1:
            return "A+ (Отлично)"
        elif response_time < 2:
            return "A (Хорошо)"
        elif response_time < 3:
            return "B (Удовлетворительно)"
        elif response_time < 5:
            return "C (Медленно)"
        else:
            return "D (Очень медленно)"
    
    def test_health_check_details(self) -> Dict[str, Any]:
        """Детальное тестирование health check"""
        print("\n🏥 Детальное тестирование health check...")
        
        result = self.test_endpoint("Detailed Health Check", f"{self.base_url}/health/")
        
        if result['success'] and 'data' in result:
            health_data = result['data']
            
            print(f"   📊 Общий статус: {health_data.get('status', 'Unknown')}")
            print(f"   📊 Время ответа: {health_data.get('response_time', 0):.2f}s")
            
            if 'checks' in health_data:
                print("   📊 Компоненты:")
                for component, check in health_data['checks'].items():
                    status = check.get('status', 'Unknown')
                    status_icon = "✅" if status == 'healthy' else "❌"
                    print(f"      {status_icon} {component}: {status}")
            
            if 'system_info' in health_data:
                sys_info = health_data['system_info']
                print(f"   📊 Использование памяти: {sys_info.get('memory_usage_mb', 0):.1f}MB")
                print(f"   📊 Время работы: {sys_info.get('uptime_seconds', 0):.0f}s")
        
        return result
    
    def generate_report(self) -> Dict[str, Any]:
        """Генерирует отчет о тестировании"""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r['success'])
        failed_tests = total_tests - successful_tests
        
        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Группируем результаты по статусу
        healthy_components = []
        unhealthy_components = []
        
        for result in self.results:
            if result['success']:
                healthy_components.append(result['name'])
            else:
                unhealthy_components.append(result['name'])
        
        report = {
            'test_summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': failed_tests,
                'success_rate': success_rate,
                'test_duration': time.time() - self.start_time
            },
            'healthy_components': healthy_components,
            'unhealthy_components': unhealthy_components,
            'detailed_results': self.results,
            'timestamp': datetime.now().isoformat(),
            'recommendations': self._get_recommendations(success_rate, unhealthy_components)
        }
        
        return report
    
    def _get_recommendations(self, success_rate: float, unhealthy_components: List[str]) -> List[str]:
        """Генерирует рекомендации на основе результатов"""
        recommendations = []
        
        if success_rate < 80:
            recommendations.append("🔴 КРИТИЧЕСКОЕ: Много компонентов не работают. Проверьте Render Dashboard.")
        
        if success_rate < 95:
            recommendations.append("🟡 ВНИМАНИЕ: Некоторые компоненты работают нестабильно.")
        
        if 'Health Check' in unhealthy_components:
            recommendations.append("🏥 Проверьте health check endpoint - возможно проблема с базой данных.")
        
        if 'Telegram Bot Webhook' in unhealthy_components:
            recommendations.append("🤖 Проверьте настройки Telegram бота и webhook.")
        
        if 'AI Chat' in unhealthy_components:
            recommendations.append("🤖 Проверьте настройки ИИ сервисов (Gemini API).")
        
        if success_rate >= 95:
            recommendations.append("✅ Система работает отлично! Все компоненты функционируют нормально.")
        
        return recommendations
    
    def print_report(self, report: Dict[str, Any]):
        """Выводит отчет в консоль"""
        print("\n" + "=" * 60)
        print("📊 ОТЧЕТ О ТЕСТИРОВАНИИ СИСТЕМЫ EXAMFLOW 2.0")
        print("=" * 60)
        
        summary = report['test_summary']
        print("📈 Общая статистика:")
        print(f"   Всего тестов: {summary['total_tests']}")
        print(f"   Успешных: {summary['successful_tests']}")
        print(f"   Неудачных: {summary['failed_tests']}")
        print(f"   Процент успеха: {summary['success_rate']:.1f}%")
        print(f"   Время тестирования: {summary['test_duration']:.1f}s")
        
        print("\n✅ Работающие компоненты (" + str(len(report['healthy_components'])) + "):")
        for component in report['healthy_components']:
            print("   - " + str(component))
        
        if report['unhealthy_components']:
            print("\n❌ Проблемные компоненты (" + str(len(report['unhealthy_components'])) + "):")
            for component in report['unhealthy_components']:
                print("   - " + str(component))
        
        print("\n💡 Рекомендации:")
        for recommendation in report['recommendations']:
            print("   " + str(recommendation))
        
        print("\n🕐 Время тестирования: " + str(report['timestamp']))
        print("=" * 60)


def main():
    """Основная функция"""
    print("🚀 Тестирование системы ExamFlow 2.0")
    print("Проверяем готовность к работе 24/7...")
    
    # Создаем тестер
    tester = SystemTester()
    
    # Выполняем все тесты
    tester.test_all_endpoints()
    tester.test_performance()
    tester.test_health_check_details()
    
    # Генерируем и выводим отчет
    report = tester.generate_report()
    tester.print_report(report)
    
    # Сохраняем отчет в файл
    with open('system_test_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("\n📄 Подробный отчет сохранен в: system_test_report.json")
    
    # Возвращаем код выхода
    if report['test_summary']['success_rate'] >= 95:
        print("\n🎉 Система готова к работе 24/7!")
        exit(0)
    else:
        print("\n⚠️ Обнаружены проблемы. Проверьте рекомендации выше.")
        exit(1)


if __name__ == "__main__":
    main()
