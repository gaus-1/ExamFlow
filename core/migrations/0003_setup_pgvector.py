# Generated manually for pgvector setup

from django.db import migrations, models
from django.contrib.postgres.operations import CreateExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_datachunk'),
    ]

    operations = [
        # Создаем расширение pgvector
        CreateExtension('vector'),
        
        # Добавляем поле embedding в DataChunk
        migrations.AddField(
            model_name='datachunk',
            name='embedding',
            field=models.TextField(blank=True, null=True, help_text='Vector embedding for semantic search'),
        ),
        
        # Создаем индекс ivfflat для быстрого поиска
        migrations.RunSQL(
            sql="CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_embedding_idx ON core_datachunk USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);",
            reverse_sql="DROP INDEX IF EXISTS datachunk_embedding_idx;",
        ),
        
        # Создаем индекс для фильтрации по предмету
        migrations.RunSQL(
            sql="CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_subject_idx ON core_datachunk (subject);",
            reverse_sql="DROP INDEX IF EXISTS datachunk_subject_idx;",
        ),
        
        # Создаем индекс для фильтрации по типу документа
        migrations.RunSQL(
            sql="CREATE INDEX CONCURRENTLY IF NOT EXISTS datachunk_document_type_idx ON core_datachunk (document_type);",
            reverse_sql="DROP INDEX IF EXISTS datachunk_document_type_idx;",
        ),
    ]
