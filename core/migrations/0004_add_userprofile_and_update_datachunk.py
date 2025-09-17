# Generated manually for UserProfile and DataChunk updates

from django.db import migrations, models
from django.conf import settings
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_setup_pgvector'),
    ]

    operations = [
        # Создаем модель UserProfile (поля DataChunk уже добавлены в 0003)
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('query_stats', models.JSONField(blank=True, default=dict, verbose_name='Статистика запросов')),
                ('recent_queries', models.JSONField(blank=True, default=list, verbose_name='Последние запросы')),
                ('preferred_subjects', models.JSONField(blank=True, default=list, verbose_name='Предпочитаемые предметы')),
                ('difficulty_preference', models.CharField(choices=[('easy', 'Легкий'), ('medium', 'Средний'), ('hard', 'Сложный')], default='medium', max_length=20, verbose_name='Предпочитаемая сложность')),
                ('subscription_type', models.CharField(choices=[('free', 'Бесплатный'), ('premium', 'Премиум')], default='free', max_length=20, verbose_name='Тип подписки')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='Дата обновления')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL, verbose_name='Пользователь')),
            ],
            options={
                'verbose_name': 'Профиль пользователя',
                'verbose_name_plural': 'Профили пользователей',
            },
        ),
    ]
