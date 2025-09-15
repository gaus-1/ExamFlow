# Generated migration for focusing on Math and Russian (simplified)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0004_focus_math_russian'),
    ]

    operations = [
        # Просто добавляем поля без сложных функций
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
    ]
