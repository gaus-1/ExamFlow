from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Subject, Topic, Task


SUBJECTS = [
    ("Математика", "ЕГЭ"),
    ("Русский язык", "ЕГЭ"),
    ("Физика", "ЕГЭ"),
    ("Химия", "ЕГЭ"),
    ("Биология", "ЕГЭ"),
    ("История", "ЕГЭ"),
    ("Обществознание", "ЕГЭ"),
    ("Информатика", "ЕГЭ"),
]


class Command(BaseCommand):
    help = "Заполняет базу демонстрационными предметами, темами и заданиями"

    def handle(self, *args, **options):
        created_subjects = 0
        created_topics = 0
        created_tasks = 0

        for name, exam_type in SUBJECTS:
            subject, s_created = Subject.objects.get_or_create(
                name=name,
                defaults={
                    "exam_type": exam_type,
                    "code": name.lower().replace(" ", "_"),
                    "description": f"Предмет {name}",
                    "is_active": True,
                },
            )
            if s_created:
                created_subjects += 1

            topic, t_created = Topic.objects.get_or_create(
                subject=subject,
                code="base",
                defaults={
                    "name": "Базовые задания",
                    "description": "Начальный раздел",
                    "order": 1,
                    "is_active": True,
                },
            )
            if t_created:
                created_topics += 1

            # Добавим 5 примеров заданий
            for i in range(1, 6):
                title = f"{name}: Пример задания {i}"
                if Task.objects.filter(title=title, subject=subject).exists():
                    continue
                Task.objects.create(
                    subject=subject,
                    topic=topic,
                    title=title,
                    description=f"Демонстрационное задание {i} по предмету {name}.",
                    difficulty=2,
                    answer="",
                    source="Demo",
                    year=timezone.now().year,
                    tags=f"{name.lower()},demo",
                    is_active=True,
                )
                created_tasks += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Готово. Предметов: +{created_subjects}, тем: +{created_topics}, заданий: +{created_tasks}"
            )
        )

from django.core.management.base import BaseCommand
from core.models import ExamType, Subject, Topic, Task
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Загружает тестовые данные для ExamFlow'

    def handle(self, *args, **options):
        self.stdout.write('Загрузка тестовых данных...')
        
        # Создаем типы экзаменов
        ege, created = ExamType.objects.get_or_create(
            code='EGE',
            defaults={
                'name': 'Единый государственный экзамен',
                'description': 'Основной экзамен для поступления в вузы'
            }
        )
        if created:
            self.stdout.write(f'✅ Создан тип экзамена: {ege.name}')
        
        oge, created = ExamType.objects.get_or_create(
            code='OGE',
            defaults={
                'name': 'Основной государственный экзамен',
                'description': 'Экзамен для получения аттестата об основном общем образовании'
            }
        )
        if created:
            self.stdout.write(f'✅ Создан тип экзамена: {oge.name}')
        
        # Создаем предметы
        subjects_data = [
            {
                'name': 'Математика', 
                'exam_type': 'ЕГЭ',
                'code': 'MATH',
                'description': 'Базовый и профильный уровни математики'
            },
            {
                'name': 'Русский язык', 
                'exam_type': 'ЕГЭ',
                'code': 'RUS',
                'description': 'Русский язык и литература'
            },
            {
                'name': 'Физика', 
                'exam_type': 'ЕГЭ',
                'code': 'PHYS',
                'description': 'Физика и астрономия'
            },
            {
                'name': 'Химия', 
                'exam_type': 'ЕГЭ',
                'code': 'CHEM',
                'description': 'Химия и химические технологии'
            },
            {
                'name': 'Биология', 
                'exam_type': 'ЕГЭ',
                'code': 'BIO',
                'description': 'Биология и биологические науки'
            },
            {
                'name': 'История', 
                'exam_type': 'ЕГЭ',
                'code': 'HIST',
                'description': 'История и исторические науки'
            },
            {
                'name': 'Обществознание', 
                'exam_type': 'ЕГЭ',
                'code': 'SOC',
                'description': 'Обществознание и социальные науки'
            },
            {
                'name': 'Информатика', 
                'exam_type': 'ЕГЭ',
                'code': 'INF',
                'description': 'Информатика и информационные технологии'
            },
            {
                'name': 'Литература', 
                'exam_type': 'ЕГЭ',
                'code': 'LIT',
                'description': 'Литература и филология'
            },
            {
                'name': 'География', 
                'exam_type': 'ЕГЭ',
                'code': 'GEO',
                'description': 'География и географические науки'
            },
        ]
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults=subject_data
            )
            if created:
                self.stdout.write(f'✅ Создан предмет: {subject.name}')
        
        # Создаем темы для математики
        math_subject = Subject.objects.get(name='Математика')
        math_topics = [
            {'name': 'Алгебра', 'code': 'MATH_ALG', 'order': 1, 'description': 'Алгебраические выражения и уравнения'},
            {'name': 'Геометрия', 'code': 'MATH_GEO', 'order': 2, 'description': 'Планиметрия и стереометрия'},
            {'name': 'Тригонометрия', 'code': 'MATH_TRIG', 'order': 3, 'description': 'Тригонометрические функции и уравнения'},
            {'name': 'Производная', 'code': 'MATH_DER', 'order': 4, 'description': 'Производная и её приложения'},
            {'name': 'Интеграл', 'code': 'MATH_INT', 'order': 5, 'description': 'Интеграл и его приложения'},
            {'name': 'Вероятность', 'code': 'MATH_PROB', 'order': 6, 'description': 'Теория вероятностей и статистика'},
        ]
        
        for topic_data in math_topics:
            topic, created = Topic.objects.get_or_create(
                name=topic_data['name'],
                subject=math_subject,
                defaults=topic_data
            )
            if created:
                self.stdout.write(f'✅ Создана тема: {topic.name}')
        
        # Создаем темы для физики
        physics_subject = Subject.objects.get(name='Физика')
        physics_topics = [
            {'name': 'Механика', 'code': 'PHYS_MECH', 'order': 1, 'description': 'Кинематика, динамика, статика'},
            {'name': 'Термодинамика', 'code': 'PHYS_THERM', 'order': 2, 'description': 'Тепловые явления и газы'},
            {'name': 'Электричество', 'code': 'PHYS_ELEC', 'order': 3, 'description': 'Электрические и магнитные явления'},
            {'name': 'Оптика', 'code': 'PHYS_OPT', 'order': 4, 'description': 'Геометрическая и волновая оптика'},
            {'name': 'Квантовая физика', 'code': 'PHYS_QUANT', 'order': 5, 'description': 'Квантовая механика и атомная физика'},
            {'name': 'Ядерная физика', 'code': 'PHYS_NUC', 'order': 6, 'description': 'Ядерные реакции и радиоактивность'},
        ]
        
        for topic_data in physics_topics:
            topic, created = Topic.objects.get_or_create(
                name=topic_data['name'],
                subject=physics_subject,
                defaults=topic_data
            )
            if created:
                self.stdout.write(f'✅ Создана тема: {topic.name}')
        
        # Создаем тестовые задания
        sample_tasks = [
            {
                'subject': math_subject,
                'topic': Topic.objects.get(name='Алгебра', subject=math_subject),
                'title': 'Решение квадратного уравнения',
                'description': 'Решите квадратное уравнение: x² - 5x + 6 = 0. Найдите все корни уравнения.',
                'difficulty': 2,
                'answer': 'x₁ = 2, x₂ = 3',
                'solution': 'Используем формулу дискриминанта: D = b² - 4ac = 25 - 24 = 1. x = (-b ± √D) / 2a = (5 ± 1) / 2. Получаем x₁ = 2, x₂ = 3.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'квадратное уравнение, дискриминант, алгебра'
            },
            {
                'subject': math_subject,
                'topic': Topic.objects.get(name='Геометрия', subject=math_subject),
                'title': 'Площадь треугольника',
                'description': 'Найдите площадь треугольника со сторонами 3, 4, 5. Определите тип треугольника.',
                'difficulty': 1,
                'answer': '6',
                'solution': 'Проверяем: 3² + 4² = 9 + 16 = 25 = 5². Это прямоугольный треугольник. Площадь = (3 × 4) / 2 = 6.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'площадь треугольника, теорема Пифагора, геометрия'
            },
            {
                'subject': physics_subject,
                'topic': Topic.objects.get(name='Механика', subject=physics_subject),
                'title': 'Кинематика - равноускоренное движение',
                'description': 'Тело движется равноускоренно с ускорением 2 м/с². Какой путь пройдет тело за 5 секунд, если начальная скорость равна 0?',
                'difficulty': 2,
                'answer': '25 метров',
                'solution': 'Используем формулу: S = v₀t + at²/2. При v₀ = 0: S = at²/2 = 2 × 25 / 2 = 25 м.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'кинематика, равноускоренное движение, механика'
            },
            {
                'subject': physics_subject,
                'topic': Topic.objects.get(name='Электричество', subject=physics_subject),
                'title': 'Закон Ома',
                'description': 'При напряжении 12 В сила тока в цепи равна 2 А. Найдите сопротивление проводника.',
                'difficulty': 1,
                'answer': '6 Ом',
                'solution': 'По закону Ома: R = U/I = 12/2 = 6 Ом.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'закон Ома, электричество, сопротивление'
            },
            {
                'subject': math_subject,
                'topic': Topic.objects.get(name='Тригонометрия', subject=math_subject),
                'title': 'Тригонометрическое уравнение',
                'description': 'Решите уравнение: sin(x) = 1/2 на промежутке [0, 2π].',
                'difficulty': 3,
                'answer': 'x₁ = π/6, x₂ = 5π/6',
                'solution': 'sin(x) = 1/2 при x = π/6 + 2πn или x = 5π/6 + 2πn. На промежутке [0, 2π] получаем x₁ = π/6, x₂ = 5π/6.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'тригонометрия, уравнение, синус'
            },
            {
                'subject': physics_subject,
                'topic': Topic.objects.get(name='Оптика', subject=physics_subject),
                'title': 'Преломление света',
                'description': 'Луч света переходит из воздуха в воду. Угол падения равен 30°. Найдите угол преломления, если показатель преломления воды равен 1.33.',
                'difficulty': 3,
                'answer': '22°',
                'solution': 'По закону Снеллиуса: n₁sin(i) = n₂sin(r). 1 × sin(30°) = 1.33 × sin(r). sin(r) = 0.5/1.33 ≈ 0.376. r ≈ arcsin(0.376) ≈ 22°.',
                'source': 'ФИПИ - ЕГЭ 2024',
                'year': 2024,
                'tags': 'оптика, преломление, закон Снеллиуса'
            }
        ]
        
        for task_data in sample_tasks:
            task, created = Task.objects.get_or_create(
                title=task_data['title'],
                subject=task_data['subject'],
                defaults=task_data
            )
            if created:
                self.stdout.write(f'✅ Создано задание: {task.title}')
        
        self.stdout.write(
            self.style.SUCCESS(
                '🎉 Загрузка тестовых данных завершена!\n'
                'Теперь вы можете:\n'
                '1. Войти в админку: /admin/\n'
                '2. Добавить больше заданий\n'
                '3. Запустить бота: python manage.py runbot\n'
                '4. Создать суперпользователя: python manage.py createsuperuser'
            )
        )

