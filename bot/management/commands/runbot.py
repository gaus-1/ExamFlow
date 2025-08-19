from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        "Запуск бота (webhook режим). Команда-заглушка для Render: "
        "бот работает через вебхуки внутри веб-процесса, отдельный процесс не требуется."
    )

    def handle(self, *args, **options):
        # Сообщаем в логах, что отдельный процесс бота не нужен
        self.stdout.write(self.style.SUCCESS(
            "[runbot] Вебхук-режим активен: отдельный процесс бота не запускается."
        ))


