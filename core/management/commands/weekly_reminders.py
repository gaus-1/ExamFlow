from django.core.management.base import BaseCommand
from core.weekly_reminders import send_weekly_inactive_reminders


class Command(BaseCommand):
    help = 'Отправить еженедельные напоминания неактивным пользователям бота'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=200, help='Максимум уведомлений за запуск')

    def handle(self, *args, **options):
        limit = options['limit']
        sent = send_weekly_inactive_reminders(limit=limit)
        self.stdout.write(self.style.SUCCESS(f'✅ Отправлено напоминаний: {sent}'))
