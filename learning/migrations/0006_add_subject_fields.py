from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('learning', '0005_simple_focus_math_russian'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='code',
            field=models.CharField(max_length=32, null=True, blank=True, db_index=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='description',
            field=models.TextField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='icon',
            field=models.CharField(max_length=8, null=True, blank=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='is_archived',
            field=models.BooleanField(default=False, db_index=True),
        ),
        migrations.AddField(
            model_name='subject',
            name='is_primary',
            field=models.BooleanField(default=False, db_index=True),
        ),
    ]


