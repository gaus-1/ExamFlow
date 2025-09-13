from django.core.management.base import BaseCommand
from django.db import transaction

class Command(BaseCommand):  # type: ignore
    help = "Инициализирует карту источников FIPI для математики и русского"

    def handle(self, *args, **options):
        try:
            from core.models import FIPISourceMap  # type: ignore
        except Exception:
            self.stdout.write(self.style.ERROR(
                "Модель FIPISourceMap недоступна"))  # type: ignore
            return

        seeds = [
                "name": "ЕГЭ Математика — Демоверсия",
                "url": "https://fipi.ru/ege/demoversii/po-matematike",
                "type": "PDF",
                "category": "demo",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
                "name": "ЕГЭ Математика — Спецификация",
                "url": "https://fipi.ru/ege/specifikacii/po-matematike",
                "type": "PDF",
                "category": "spec",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
                "name": "ЕГЭ Математика — Кодификатор",
                "url": "https://fipi.ru/ege/kodifikatory/po-matematike",
                "type": "PDF",
                "category": "codifier",
                "subject": "Математика",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 90,
            },
                "name": "ЕГЭ Русский — Демоверсия",
                "url": "https://fipi.ru/ege/demoversii/po-russkomu-yazyku",
                "type": "PDF",
                "category": "demo",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
                "name": "ЕГЭ Русский — Спецификация",
                "url": "https://fipi.ru/ege/specifikacii/po-russkomu-yazyku",
                "type": "PDF",
                "category": "spec",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 100,
            },
                "name": "ЕГЭ Русский — Кодификатор",
                "url": "https://fipi.ru/ege/kodifikatory/po-russkomu-yazyku",
                "type": "PDF",
                "category": "codifier",
                "subject": "Русский язык",
                "exam_type": "ЕГЭ",
                "update_frequency": "yearly",
                "priority": 90,
            },
        ]

        created = 0
        with transaction.atomic():  # type: ignore
            for s in seeds:
                obj, was_created = FIPISourceMap.objects.get_or_create(  # type: ignore
                    url=s["url"], defaults=s
                )
                if was_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(
                "Готово: добавлено {created} источников (или уже были).")  # type: ignore
        )
