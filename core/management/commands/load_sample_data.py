from django.core.management.base import BaseCommand
from learning.models import Subject, Topic, Task
from django.db import transaction


class Command(BaseCommand):
    help = 'Загружает образцы данных для ExamFlow'

    def handle(self, *args, **options):
        self.stdout.write('📚 ЗАГРУЗКА ОБРАЗЦОВ ДАННЫХ EXAMFLOW')
        self.stdout.write('=' * 50)
        
        try:
            with transaction.atomic():
                # Создаем предметы если их нет
                if Subject.objects.count() == 0:  # type: ignore
                    self.stdout.write('📖 Создаем предметы...')
                    
                    subjects_data = [
                        {'name': 'Математика'},
                        {'name': 'Физика'},
                        {'name': 'Химия'},
                        {'name': 'Биология'},
                        {'name': 'История'},
                        {'name': 'География'},
                        {'name': 'Литература'},
                        {'name': 'Информатика'}
                    ]
                    
                    subjects = []
                    for data in subjects_data:
                        subject = Subject(**data)
                        subjects.append(subject)
                    Subject.objects.bulk_create(subjects)  # type: ignore
                    self.stdout.write(self.style.SUCCESS(f'✅ Создано {len(subjects)} предметов'))  # type: ignore
                    
                    # Создаем темы для математики
                    math_subject = Subject.objects.get(name='Математика')  # type: ignore
                    topics_data = [
                        {'name': 'Алгебра', 'subject': math_subject, 'code': 'ALG001'},
                        {'name': 'Геометрия', 'subject': math_subject, 'code': 'GEO001'},
                        {'name': 'Тригонометрия', 'subject': math_subject, 'code': 'TRIG001'}
                    ]
                    
                    topics = []
                    for data in topics_data:
                        topic = Topic(**data)
                        topics.append(topic)
                    Topic.objects.bulk_create(topics)  # type: ignore
                    self.stdout.write(self.style.SUCCESS(f'✅ Создано {len(topics)} тем для математики'))  # type: ignore
                    
                    # Создаем образцы заданий
                    self.stdout.write('📝 Создаем образцы заданий...')
                    tasks_data = [
                        {
                            'title': 'Решите квадратное уравнение: x² + 5x + 6 = 0',
                            'description': 'Найдите корни квадратного уравнения x² + 5x + 6 = 0',
                            'answer': 'x₁ = -2, x₂ = -3',
                            'difficulty': 2,
                            'subject': math_subject
                        },
                        {
                            'title': 'Найдите площадь прямоугольника со сторонами 5 и 8',
                            'description': 'Вычислите площадь прямоугольника, если его стороны равны 5 и 8 единиц',
                            'answer': '40 квадратных единиц',
                            'difficulty': 1,
                            'subject': math_subject
                        }
                    ]
                    
                    tasks = []
                    for data in tasks_data:
                        task = Task(**data)
                        tasks.append(task)
                    
                    Task.objects.bulk_create(tasks)  # type: ignore
                    self.stdout.write(self.style.SUCCESS(f'✅ Создано {len(tasks)} образцов заданий'))  # type: ignore
                    
                else:
                    self.stdout.write('ℹ️ Данные уже существуют, пропускаем создание')
                
                # Показываем статистику
                self.stdout.write('📊 СТАТИСТИКА БАЗЫ ДАННЫХ:')
                self.stdout.write(f'   Предметы: {Subject.objects.count()}')  # type: ignore
                self.stdout.write(f'   Темы: {Topic.objects.count()}')  # type: ignore
                self.stdout.write(f'   Задания: {Task.objects.count()}')  # type: ignore
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Ошибка при загрузке данных: {e}'))  # type: ignore
            return
        
        self.stdout.write('=' * 50)
        self.stdout.write(self.style.SUCCESS('🎉 ОБРАЗЦЫ ДАННЫХ ЗАГРУЖЕНЫ!'))  # type: ignore
        self.stdout.write('✅ База данных готова к работе')
        self.stdout.write('✅ Сайт должен работать без ошибок')