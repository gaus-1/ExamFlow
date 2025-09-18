from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0005_simple_focus_math_russian'),
    ]

    # Поля уже добавлены в 0004_focus_math_russian, делаем no-op для совместимости
    operations = []


