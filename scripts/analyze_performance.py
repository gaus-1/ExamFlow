#!/usr/bin/env python
"""
Анализ производительности ExamFlow
Выявляет узкие места и предлагает оптимизации
"""

import os
import sys
import time
import cProfile
import pstats
import io
from pathlib import Path

# Настройка Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'examflow_project.settings')

try:
    import django
    django.setup()

    from core.container import Container
    from learning.models import Subject, Task
    from django.test import RequestFactory
    from learning.views import home

except ImportError as e:
    print(f"⚠️ Django не настроен: {e}")
    sys.exit(1)


class PerformanceAnalyzer:
    """Анализатор производительности ExamFlow"""

    def __init__(self):
        self.results = {}
        self.factory = RequestFactory()

    def analyze_ai_performance(self):
        """Анализирует производительность AI системы"""
        print("🤖 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ AI:")

        try:
            ai_orchestrator = Container.ai_orchestrator()

            # Тестируем скорость AI запросов
            test_prompts = [
                "Что такое производная?",
                "Как решать квадратные уравнения?",
                "Объясни интегралы"
            ]

            times = []
            for prompt in test_prompts:
                start_time = time.time()
                try:
                    response = ai_orchestrator.ask(prompt)
                    end_time = time.time()

                    if response and 'answer' in response:
                        duration = end_time - start_time
                        times.append(duration)
                        print(f"  ✅ Запрос выполнен за {duration:.2f}с")
                    else:
                        print("  ❌ Некорректный ответ")

                except Exception as e:
                    print(f"  ❌ Ошибка: {e}")

            if times:
                avg_time = sum(times) / len(times)
                max_time = max(times)
                min_time = min(times)

                print(f"  📊 Среднее время: {avg_time:.2f}с")
                print(f"  📊 Максимальное: {max_time:.2f}с")
                print(f"  📊 Минимальное: {min_time:.2f}с")

                self.results['ai_avg_time'] = avg_time
                self.results['ai_max_time'] = max_time

                # Оценка производительности
                if avg_time < 2.0:
                    print("  🟢 Производительность AI: ОТЛИЧНАЯ")
                elif avg_time < 5.0:
                    print("  🟡 Производительность AI: ХОРОШАЯ")
                else:
                    print("  🔴 Производительность AI: ТРЕБУЕТ ОПТИМИЗАЦИИ")

        except Exception as e:
            print(f"  ❌ Ошибка анализа AI: {e}")

    def analyze_view_performance(self):
        """Анализирует производительность представлений Django"""
        print("\n🌐 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ ПРЕДСТАВЛЕНИЙ:")

        try:
            # Профилируем главную страницу
            request = self.factory.get('/')

            # Используем cProfile для детального анализа
            profiler = cProfile.Profile()

            start_time = time.time()
            profiler.enable()

            response = home(request)

            profiler.disable()
            end_time = time.time()

            total_time = end_time - start_time
            print(f"  ✅ Главная страница: {total_time:.3f}с")

            # Анализируем профиль
            s = io.StringIO()
            ps = pstats.Stats(profiler, stream=s)
            ps.sort_stats('cumulative')
            ps.print_stats(10)  # Топ 10 функций

            profile_output = s.getvalue()

            # Ищем медленные функции
            slow_functions = []
            for line in profile_output.split('\n')[5:15]:  # Пропускаем заголовки
                if line.strip() and 'function calls' not in line:
                    parts = line.split()
                    if len(parts) >= 4:
                        try:
                            cumtime = float(parts[3])
                            if cumtime > 0.1:  # Функции медленнее 100ms
                                slow_functions.append((parts[-1], cumtime))
                        except (ValueError, IndexError):
                            pass

            if slow_functions:
                print("  ⚠️ Медленные функции:")
                for func_name, time_spent in slow_functions[:5]:
                    print(f"    - {func_name}: {time_spent:.3f}с")
            else:
                print("  ✅ Медленных функций не найдено")

            self.results['view_time'] = total_time

            # Оценка
            if total_time < 0.1:
                print("  🟢 Производительность представлений: ОТЛИЧНАЯ")
            elif total_time < 0.5:
                print("  🟡 Производительность представлений: ХОРОШАЯ")
            else:
                print("  🔴 Производительность представлений: ТРЕБУЕТ ОПТИМИЗАЦИИ")

        except Exception as e:
            print(f"  ❌ Ошибка анализа представлений: {e}")

    def analyze_database_queries(self):
        """Анализирует производительность запросов к БД"""
        print("\n🗄️ АНАЛИЗ ЗАПРОСОВ К БАЗЕ ДАННЫХ:")

        try:
            from django.db import connection
            from django.test.utils import override_settings

            # Включаем логирование запросов
            with override_settings(LOGGING_CONFIG=None):
                # Сбрасываем счетчик запросов
                connection.queries_log.clear()

                start_time = time.time()

                # Выполняем типичные операции
                subjects = list(Subject.objects.filter(is_archived=False)[:10])
                tasks = list(Task.objects.select_related('subject')[:20])

                end_time = time.time()

                query_count = len(connection.queries)
                total_time = end_time - start_time

                print(f"  📊 Количество запросов: {query_count}")
                print(f"  📊 Время выполнения: {total_time:.3f}с")
                print(f"  📊 Среднее время на запрос: {total_time/query_count:.3f}с")

                # Анализируем медленные запросы
                slow_queries = []
                for query in connection.queries:
                    try:
                        query_time = float(query['time'])
                        if query_time > 0.01:  # Запросы медленнее 10ms
                            slow_queries.append((query['sql'][:100], query_time))
                    except (KeyError, ValueError):
                        pass

                if slow_queries:
                    print("  ⚠️ Медленные запросы:")
                    for sql, query_time in slow_queries[:3]:
                        print(f"    - {sql}... : {query_time:.3f}с")
                else:
                    print("  ✅ Медленных запросов не найдено")

                self.results['db_queries'] = query_count
                self.results['db_time'] = total_time

                # Оценка
                if query_count < 10 and total_time < 0.1:
                    print("  🟢 Производительность БД: ОТЛИЧНАЯ")
                elif query_count < 20 and total_time < 0.5:
                    print("  🟡 Производительность БД: ХОРОШАЯ")
                else:
                    print("  🔴 Производительность БД: ТРЕБУЕТ ОПТИМИЗАЦИИ")

        except Exception as e:
            print(f"  ❌ Ошибка анализа БД: {e}")

    def analyze_file_sizes(self):
        """Анализирует размеры файлов проекта"""
        print("\n📁 АНАЛИЗ РАЗМЕРОВ ФАЙЛОВ:")

        try:
            project_root = Path(__file__).parent.parent

            # Анализируем размеры по типам файлов
            file_stats = {
                'python': {'count': 0, 'size': 0, 'extensions': ['.py']},
                'templates': {'count': 0, 'size': 0, 'extensions': ['.html']},
                'css': {'count': 0, 'size': 0, 'extensions': ['.css']},
                'javascript': {'count': 0, 'size': 0, 'extensions': ['.js']},
                'static': {'count': 0, 'size': 0, 'extensions': ['.png', '.jpg', '.svg', '.ico']},
            }

            for file_path in project_root.rglob('*'):
                if file_path.is_file() and not any(part.startswith('.') for part in file_path.parts):
                    file_size = file_path.stat().st_size
                    file_ext = file_path.suffix.lower()

                    for file_type, stats in file_stats.items():
                        if file_ext in stats['extensions']:
                            stats['count'] += 1
                            stats['size'] += file_size
                            break

            # Выводим статистику
            total_size = sum(stats['size'] for stats in file_stats.values())

            for file_type, stats in file_stats.items():
                if stats['count'] > 0:
                    size_mb = stats['size'] / 1024 / 1024
                    percentage = (stats['size'] / total_size) * 100 if total_size > 0 else 0
                    print(f"  📊 {file_type.title()}: {stats['count']} файлов, {size_mb:.1f}MB ({percentage:.1f}%)")

            total_mb = total_size / 1024 / 1024
            print(f"  📊 Общий размер: {total_mb:.1f}MB")

            # Рекомендации
            if total_mb > 100:
                print("  🔴 Проект слишком большой - требуется очистка")
            elif total_mb > 50:
                print("  🟡 Размер проекта средний - можно оптимизировать")
            else:
                print("  🟢 Размер проекта оптимальный")

        except Exception as e:
            print(f"  ❌ Ошибка анализа файлов: {e}")

    def generate_recommendations(self):
        """Генерирует рекомендации по оптимизации"""
        print("\n💡 РЕКОМЕНДАЦИИ ПО ОПТИМИЗАЦИИ:")

        # AI рекомендации
        if 'ai_avg_time' in self.results:
            if self.results['ai_avg_time'] > 3.0:
                print("  🔧 AI: Добавить более агрессивное кэширование")
                print("  🔧 AI: Рассмотреть асинхронную обработку")

        # БД рекомендации
        if 'db_queries' in self.results:
            if self.results['db_queries'] > 15:
                print("  🔧 БД: Добавить select_related() и prefetch_related()")
                print("  🔧 БД: Рассмотреть денормализацию для часто используемых данных")

        # Общие рекомендации
        print("  ✅ Продолжить использование Redis кэширования")
        print("  ✅ Рассмотреть CDN для статических файлов")
        print("  ✅ Добавить мониторинг производительности")

    def run_full_analysis(self):
        """Запускает полный анализ производительности"""
        print("🔍 АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ EXAMFLOW")
        print("=" * 60)

        self.analyze_ai_performance()
        self.analyze_view_performance()
        self.analyze_database_queries()
        self.analyze_file_sizes()
        self.generate_recommendations()

        print("\n✅ Анализ производительности завершен")


def main():
    """Главная функция"""
    analyzer = PerformanceAnalyzer()
    analyzer.run_full_analysis()


if __name__ == "__main__":
    main()
