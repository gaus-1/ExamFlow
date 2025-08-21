from django.db import migrations

class Migration(migrations.Migration):
    
    dependencies = [
        ('core', '0008_add_current_task_id_to_userprofile'),
    ]

    operations = [
        migrations.RunSQL(
            sql=(
                "ALTER TABLE core_userprofile "
                "ADD COLUMN IF NOT EXISTS current_task_id integer NULL;"
            ),
            reverse_sql=(
                "ALTER TABLE core_userprofile "
                "DROP COLUMN IF EXISTS current_task_id;"
            ),
        ),
    ]
