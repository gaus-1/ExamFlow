# Generated migration for focusing on Math and Russian

from django.db import migrations, models


def archive_unused_subjects(apps, schema_editor):
    """Архивирует ненужные предметы"""
    Subject = apps.get_model('learning', 'Subject')
    
    unused_subjects = [
        'Физика', 'Химия', 'Биология', 'История', 'География',
        'Литература', 'Информатика', 'Обществознание',
        'Английский язык', 'Немецкий язык', 'Французский язык', 'Испанский язык'
    ]
    
    for subject_name in unused_subjects:
        Subject.objects.filter(name=subject_name).update(is_archived=True)
    
    print(f"Архивировано {len(unused_subjects)} предметов")


def restore_unused_subjects(apps, schema_editor):
    """Восстанавливает архивированные предметы"""
    Subject = apps.get_model('learning', 'Subject')
    Subject.objects.filter(is_archived=True).update(is_archived=False)


def create_math_variants(apps, schema_editor):
    """Создает варианты математики"""
    Subject = apps.get_model('learning', 'Subject')
    
    math_variants = [
        {
            'name': 'Математика (профильная)',
            'code': 'math_prof',
            'exam_type': 'ЕГЭ',
            'description': 'Профильная математика ЕГЭ - задания 1-19',
            'icon': '📐',
            'is_primary': True
        },
        {
            'name': 'Математика (непрофильная)',
            'code': 'math_base',
            'exam_type': 'ЕГЭ',
            'description': 'Базовая математика ЕГЭ - задания 1-20',
            'icon': '📊',
            'is_primary': True
        },
        {
            'name': 'Математика (ОГЭ)',
            'code': 'math_oge',
            'exam_type': 'ОГЭ',
            'description': 'Математика ОГЭ - задания 1-26',
            'icon': '🔢',
            'is_primary': True
        },
    ]
    
    for variant in math_variants:
        subject, created = Subject.objects.get_or_create(
            name=variant['name'],
            defaults={
                'code': variant['code'],
                'exam_type': variant['exam_type'],
                'description': variant['description'],
                'icon': variant['icon'],
                'is_primary': variant['is_primary']
            }
        )
        if created:
            print(f"Создан предмет: {subject.name}")


def remove_math_variants(apps, schema_editor):
    """Удаляет варианты математики"""
    Subject = apps.get_model('learning', 'Subject')
    math_codes = ['math_prof', 'math_base', 'math_oge']
    Subject.objects.filter(code__in=math_codes).delete()


def create_russian_variants(apps, schema_editor):
    """Создает варианты русского языка"""
    Subject = apps.get_model('learning', 'Subject')
    
    russian_variants = [
        {
            'name': 'Русский язык (ЕГЭ)',
            'code': 'russian_ege',
            'exam_type': 'ЕГЭ',
            'description': 'Русский язык ЕГЭ - сочинение, тесты, грамматика',
            'icon': '📝',
            'is_primary': True
        },
        {
            'name': 'Русский язык (ОГЭ)',
            'code': 'russian_oge',
            'exam_type': 'ОГЭ',
            'description': 'Русский язык ОГЭ - изложение, сочинение, тесты',
            'icon': '📖',
            'is_primary': True
        },
    ]
    
    for variant in russian_variants:
        subject, created = Subject.objects.get_or_create(
            name=variant['name'],
            defaults={
                'code': variant['code'],
                'exam_type': variant['exam_type'],
                'description': variant['description'],
                'icon': variant['icon'],
                'is_primary': variant['is_primary']
            }
        )
        if created:
            print(f"Создан предмет: {subject.name}")


def remove_russian_variants(apps, schema_editor):
    """Удаляет варианты русского языка"""
    Subject = apps.get_model('learning', 'Subject')
    russian_codes = ['russian_ege', 'russian_oge']
    Subject.objects.filter(code__in=russian_codes).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0003_alter_userprogress_user'),
    ]

    operations = [
        # Добавляем поля для архивации и приоритета
        migrations.AddField(
            model_name='subject',
            name='code',
            field=models.CharField(max_length=20, unique=True, blank=True, null=True, verbose_name='Код предмета'),
        ),
        migrations.AddField(
            model_name='subject',
            name='description',
            field=models.TextField(blank=True, verbose_name='Описание'),
        ),
        migrations.AddField(
            model_name='subject',
            name='icon',
            field=models.CharField(max_length=50, blank=True, verbose_name='Иконка'),
        ),
        migrations.AddField(
            model_name='subject',
            name='is_archived',
            field=models.BooleanField(default=False, verbose_name='Архивирован'),
        ),
        migrations.AddField(
            model_name='subject',
            name='is_primary',
            field=models.BooleanField(default=False, verbose_name='Основной предмет'),
        ),
        migrations.AddField(
            model_name='subject',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, verbose_name='Дата создания'),
        ),
        migrations.AddField(
            model_name='subject',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, verbose_name='Дата обновления'),
        ),
        
        # Архивируем ненужные предметы
        migrations.RunPython(
            code=archive_unused_subjects,
            reverse_code=restore_unused_subjects,
        ),
        
        # Создаем варианты математики
        migrations.RunPython(
            code=create_math_variants,
            reverse_code=remove_math_variants,
        ),
        
        # Создаем варианты русского языка
        migrations.RunPython(
            code=create_russian_variants,
            reverse_code=remove_russian_variants,
        ),
    ]
