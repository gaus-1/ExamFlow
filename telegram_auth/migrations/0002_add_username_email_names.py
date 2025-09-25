from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("telegram_auth", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="telegramuser",
            name="username",
            field=models.CharField(max_length=150, blank=True, default="", unique=False),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="telegramuser",
            name="email",
            field=models.EmailField(max_length=254, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="telegramuser",
            name="first_name",
            field=models.CharField(max_length=150, blank=True, default=""),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="telegramuser",
            name="last_name",
            field=models.CharField(max_length=150, blank=True, default=""),
            preserve_default=False,
        ),
    ]


