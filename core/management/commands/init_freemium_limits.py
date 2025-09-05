"""
Команда для инициализации лимитов FREEMIUM
"""

from django.core.management.base import BaseCommand
from core.freemium.models import SubscriptionLimit


class Command(BaseCommand):
    help = 'Инициализация лимитов для FREEMIUM системы'

    def handle(self, *args, **options):
        # Создаем лимиты для бесплатного тарифа
        free_limits, created = SubscriptionLimit.objects.get_or_create(
            subscription_type='free',
            defaults={
                'daily_ai_requests': 10,
                'max_subjects': 0,  # без ограничений
                'has_priority_support': False,
                'has_advanced_analytics': False,
                'has_exclusive_content': False,
                'has_personal_curator': False,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Созданы лимиты для бесплатного тарифа')
            )
        else:
            self.stdout.write('Лимиты для бесплатного тарифа уже существуют')
        
        # Создаем лимиты для премиум тарифа
        premium_limits, created = SubscriptionLimit.objects.get_or_create(
            subscription_type='premium',
            defaults={
                'daily_ai_requests': 999999,  # безлимитно
                'max_subjects': 0,  # без ограничений
                'has_priority_support': True,
                'has_advanced_analytics': True,
                'has_exclusive_content': True,
                'has_personal_curator': True,
            }
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS('Созданы лимиты для премиум тарифа')
            )
        else:
            self.stdout.write('Лимиты для премиум тарифа уже существуют')
        
        self.stdout.write(
            self.style.SUCCESS('Инициализация лимитов FREEMIUM завершена')
        )
