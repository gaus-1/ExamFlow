# Generated manually for pgvector setup

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0015_fipidata_datachunk'),
    ]

    operations = [
        # Добавляем поля в DataChunk (без pgvector)
        migrations.AddField(
            model_name='datachunk',
            name='embedding_vector',
            field=models.TextField(blank=True, null=True, help_text='Vector embedding for semantic search (pgvector)'),
        ),
        
        migrations.AddField(
            model_name='datachunk',
            name='subject',
            field=models.CharField(blank=True, max_length=50, verbose_name='Предмет'),
        ),
        
        migrations.AddField(
            model_name='datachunk',
            name='document_type',
            field=models.CharField(blank=True, max_length=50, verbose_name='Тип документа'),
        ),
        
        # Создаем обычные индексы (без pgvector)
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS datachunk_subject_idx ON core_datachunk (subject);",
            reverse_sql="DROP INDEX IF EXISTS datachunk_subject_idx;",
        ),
        
        migrations.RunSQL(
            sql="CREATE INDEX IF NOT EXISTS datachunk_document_type_idx ON core_datachunk (document_type);",
            reverse_sql="DROP INDEX IF EXISTS datachunk_document_type_idx;",
        ),
    ]
