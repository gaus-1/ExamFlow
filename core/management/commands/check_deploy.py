from django.core.management.base import BaseCommand
from django.core.management import execute_from_command_line
from django.conf import settings
import os

class Command(BaseCommand):
    help = 'Проверка готовности к деплою'

    def handle(self, *args, **options):
        self.stdout.write('🔍 Проверяем готовность к деплою...')
        
        # Проверяем настройки
        self.stdout.write('✅ DEBUG = {}'.format(settings.DEBUG))
        self.stdout.write('✅ ALLOWED_HOSTS = {}'.format(settings.ALLOWED_HOSTS))
        self.stdout.write('✅ STATIC_URL = {}'.format(settings.STATIC_URL))
        self.stdout.write('✅ STATIC_ROOT = {}'.format(settings.STATIC_ROOT))
        
        # Проверяем переменные окружения
        self.stdout.write('✅ SECRET_KEY установлен: {}'.format(
            'Да' if not settings.SECRET_KEY.startswith('django-insecure') else 'НЕТ!'
        ))
        
        # Проверяем базу данных
        try:
            from django.db import connection
            cursor = connection.cursor()
            self.stdout.write('✅ База данных доступна')
        except Exception as e:
            self.stdout.write('❌ Ошибка базы данных: {}'.format(e))
        
        self.stdout.write('🎉 Проверка завершена!')
