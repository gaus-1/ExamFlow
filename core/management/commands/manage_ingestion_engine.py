"""
Команда для управления движком сбора данных
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
import logging
import json
import time

from core.data_ingestion.ingestion_engine import get_ingestion_engine, TaskPriority
from core.data_ingestion.scheduler import get_scheduler

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Управляет движком сбора данных'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=['start', 'stop', 'status', 'add-tasks', 'stats'],
            help='Действие для выполнения'
        )
        parser.add_argument(
            '--priority',
            type=int,
            choices=[1, 2, 3, 4],
            help='Приоритет для добавления задач (1=критический, 2=высокий, 3=средний, 4=низкий)'
        )
        parser.add_argument(
            '--source-ids',
            nargs='+',
            help='ID источников для добавления задач'
        )
        parser.add_argument(
            '--with-scheduler',
            action='store_true',
            help='Запустить с планировщиком'
        )
        parser.add_argument(
            '--monitor',
            action='store_true',
            help='Мониторить работу в реальном времени'
        )
    
    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            self.start_engine(options)
        elif action == 'stop':
            self.stop_engine(options)
        elif action == 'status':
            self.show_status(options)
        elif action == 'add-tasks':
            self.add_tasks(options)
        elif action == 'stats':
            self.show_statistics(options)
    
    def start_engine(self, options):
        """Запускает движок сбора данных"""
        self.stdout.write(
            self.style.SUCCESS('🚀 Запуск движка сбора данных...') # type: ignore
        )
        
        try:
            if options['with_scheduler']:
                # Запускаем с планировщиком
                scheduler = get_scheduler()
                scheduler.start()
                self.stdout.write(
                    self.style.SUCCESS('✅ Движок сбора данных и планировщик запущены') # type: ignore
                )
            else:
                # Запускаем только движок
                engine = get_ingestion_engine()
                engine.start()
                self.stdout.write(
                    self.style.SUCCESS('✅ Движок сбора данных запущен') # type: ignore
                )
            
            if options['monitor']:
                self.monitor_engine()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при запуске: {e}') # type: ignore
            )
            logger.error(f'Ошибка при запуске движка: {e}')
    
    def stop_engine(self, options):
        """Останавливает движок сбора данных"""
        self.stdout.write(
            self.style.WARNING('🛑 Остановка движка сбора данных...') # type: ignore
        )
        
        try:
            if options['with_scheduler']:
                # Останавливаем планировщик
                from core.data_ingestion.scheduler import stop_scheduler
                stop_scheduler()
                self.stdout.write(
                    self.style.SUCCESS('✅ Движок сбора данных и планировщик остановлены') # type: ignore
                )
            else:
                # Останавливаем только движок
                from core.data_ingestion.ingestion_engine import stop_ingestion_engine
                stop_ingestion_engine()
                self.stdout.write(
                    self.style.SUCCESS('✅ Движок сбора данных остановлен') # type: ignore
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при остановке: {e}') # type: ignore
            )
            logger.error(f'Ошибка при остановке движка: {e}')
    
    def show_status(self, options):
        """Показывает статус движка"""
        self.stdout.write(
            self.style.SUCCESS('📊 Статус движка сбора данных') # type: ignore
        )
        self.stdout.write('=' * 60)
        
        try:
            if options['with_scheduler']:
                scheduler = get_scheduler()
                status = scheduler.get_job_status()
                
                self.stdout.write(f'Планировщик: {"🟢 Запущен" if status["scheduler_running"] else "🔴 Остановлен"}') # type: ignore
                self.stdout.write(f'Движок: {"🟢 Запущен" if status["engine_stats"]["is_running"] else "🔴 Остановлен"}') # type: ignore
                
                self.stdout.write('\n📋 Запланированные задачи:')
                for job in status['jobs']:
                    next_run = job['next_run_time'] or 'Не запланировано'
                    self.stdout.write(f'  • {job["name"]}: {next_run}')
                
            else:
                engine = get_ingestion_engine()
                stats = engine.get_statistics()
                
                self.stdout.write(f'Движок: {"🟢 Запущен" if stats["is_running"] else "🔴 Остановлен"}') # type: ignore
                
                if stats['is_running']:
                    self.stdout.write('\n👷 Воркеры:')
                    for worker in stats['worker_stats']:
                        status_icon = "🟢" if worker['is_running'] else "🔴"
                        current_task = worker['current_task'] or "Без задач"
                        self.stdout.write(f'  • {worker["worker_id"]}: {status_icon} {current_task}')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при получении статуса: {e}') # type: ignore    
            )
    
    def add_tasks(self, options):
        """Добавляет задачи в очередь"""
        self.stdout.write(
            self.style.SUCCESS('➕ Добавление задач в очередь...') # type: ignore
        )
        
        try:
            engine = get_ingestion_engine()
            
            # Определяем приоритет
            priority = None
            if options['priority']:
                priority = TaskPriority(options['priority'])
            
            # Добавляем задачи
            count = engine.add_source_tasks(
                source_ids=options.get('source_ids'),
                priority_filter=priority
            )
            
            self.stdout.write(
                self.style.SUCCESS(f'✅ Добавлено {count} задач в очередь') # type: ignore
            )
            
            # Показываем статистику очереди
            stats = engine.get_statistics()
            self.stdout.write('\n📊 Статистика очереди:')
            for priority_name, queue_size in stats['queue_stats'].items():
                self.stdout.write(f'  • {priority_name}: {queue_size} задач')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при добавлении задач: {e}') # type: ignore
            )
    
    def show_statistics(self, options):
        """Показывает подробную статистику"""
        self.stdout.write(
            self.style.SUCCESS('📈 Подробная статистика движка') # type: ignore
        )
        self.stdout.write('=' * 60)
        
        try:
            if options['with_scheduler']:
                scheduler = get_scheduler()
                status = scheduler.get_job_status()
                
                # Статистика планировщика
                self.stdout.write('📅 Планировщик:')
                self.stdout.write(f'  Статус: {"🟢 Запущен" if status["scheduler_running"] else "🔴 Остановлен"}')
                self.stdout.write(f'  Задач: {len(status["jobs"])}')
                
                # Статистика движка
                engine_stats = status['engine_stats']
                self.stdout.write('\n🔧 Движок:')
                self.stdout.write(f'  Статус: {"🟢 Запущен" if engine_stats["is_running"] else "🔴 Остановлен"}')
                
                if engine_stats['is_running']:
                    # Статистика очередей
                    self.stdout.write('\n📋 Очереди задач:')
                    for priority, size in engine_stats['queue_stats'].items():
                        self.stdout.write(f'  • {priority}: {size} задач')
                    
                    # Статистика воркеров
                    self.stdout.write('\n👷 Воркеры:')
                    for worker in engine_stats['worker_stats']:
                        status_icon = "🟢" if worker['is_running'] else "🔴"
                        current_task = worker['current_task'] or "Без задач"
                        self.stdout.write(f'  • {worker["worker_id"]}: {status_icon} {current_task}')
                    
                    # Статистика задач
                    task_stats = engine_stats['task_stats']
                    self.stdout.write('\n📊 Статистика задач:')
                    self.stdout.write(f'  Всего: {task_stats["total"]}')
                    
                    if task_stats['by_status']:
                        self.stdout.write('  По статусам:')
                        for status, count in task_stats['by_status'].items():
                            self.stdout.write(f'    • {status}: {count}')
                    
                    if task_stats['by_priority']:
                        self.stdout.write('  По приоритетам:')
                        for priority, count in task_stats['by_priority'].items():
                            self.stdout.write(f'    • {priority}: {count}')
            
            else:
                engine = get_ingestion_engine()
                stats = engine.get_statistics()
                
                # Выводим JSON для детального анализа
                self.stdout.write('\n📄 Детальная статистика (JSON):')
                self.stdout.write(json.dumps(stats, indent=2, default=str))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка при получении статистики: {e}') # type: ignore
            )
    
    def monitor_engine(self):
        """Мониторит работу движка в реальном времени"""
        self.stdout.write(
            self.style.SUCCESS('👁️ Мониторинг движка (Ctrl+C для выхода)') # type: ignore
        )
        
        try:
            while True:
                # Очищаем экран (работает в большинстве терминалов)
                print('\033[2J\033[H', end='')
                
                # Получаем статистику
                if hasattr(self, '_scheduler'):
                    status = self._scheduler.get_job_status() # type: ignore
                    engine_stats = status['engine_stats']
                else:
                    engine = get_ingestion_engine()
                    engine_stats = engine.get_statistics()
                
                # Выводим заголовок
                self.stdout.write(
                    self.style.SUCCESS(f'📊 Мониторинг движка - {timezone.now().strftime("%H:%M:%S")}') # type: ignore
                )
                self.stdout.write('=' * 60)
                
                # Статус движка
                status_icon = "🟢" if engine_stats['is_running'] else "🔴"
                self.stdout.write(f'Движок: {status_icon} {"Запущен" if engine_stats["is_running"] else "Остановлен"}') # type: ignore
                
                if engine_stats['is_running']:
                    # Очереди
                    self.stdout.write('\n📋 Очереди:')
                    for priority, size in engine_stats['queue_stats'].items():
                        self.stdout.write(f'  {priority}: {size}')
                    
                    # Воркеры
                    self.stdout.write('\n👷 Воркеры:')
                    for worker in engine_stats['worker_stats']:
                        status_icon = "🟢" if worker['is_running'] else "🔴"
                        current_task = worker['current_task'] or "Без задач"
                        self.stdout.write(f'  {worker["worker_id"]}: {status_icon} {current_task}')
                    
                    # Задачи
                    task_stats = engine_stats['task_stats']
                    self.stdout.write(f'\n📊 Задач: {task_stats["total"]}')
                    for status, count in task_stats['by_status'].items():
                        self.stdout.write(f'  {status}: {count}')
                
                time.sleep(2)
                
        except KeyboardInterrupt:
            self.stdout.write('\n' + self.style.SUCCESS('👋 Мониторинг остановлен')) # type: ignore
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Ошибка в мониторинге: {e}') # type: ignore
            )
