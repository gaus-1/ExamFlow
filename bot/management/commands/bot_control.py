from django.core.management.base import BaseCommand
from bot.tasks import start_bot, stop_bot, restart_bot, get_bot_status

class Command(BaseCommand):
    help = 'Control Telegram bot (start|stop|restart|status)'

    def add_arguments(self, parser):
        parser.add_argument('action', choices=['start', 'stop', 'restart', 'status'],
                           help='Action to perform on the bot')

    def handle(self, *args, **options):
        action = options['action']
        
        if action == 'start':
            if start_bot():
                self.stdout.write(self.style.SUCCESS('Bot started successfully'))
            else:
                self.stdout.write(self.style.ERROR('Failed to start bot'))
        
        elif action == 'stop':
            stop_bot()
            self.stdout.write(self.style.SUCCESS('Bot stopped'))
        
        elif action == 'restart':
            if restart_bot():
                self.stdout.write(self.style.SUCCESS('Bot restarted successfully'))
            else:
                self.stdout.write(self.style.ERROR('Failed to restart bot'))
        
        elif action == 'status':
            status = get_bot_status()
            self.stdout.write(f"Bot status: {status['status']}")
            if status['status'] == 'running':
                self.stdout.write(f"PID: {status['pid']}")
